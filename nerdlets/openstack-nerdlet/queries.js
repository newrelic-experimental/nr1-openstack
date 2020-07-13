const accountId = '739516';

const nrql = `SELECT
    latest(entityGuid) AS entityGuid,
    (average(local_gb_used)/average(local_gb))*100 AS diskUsedPct,
    (average(memory_mb_used)/average(memory_mb))*100 AS memoryUsedPct,
    average(running_vms) AS runningVMs,
    average(vcpus_used) AS usedVCPUs,
    average(\`memory-actual\`) AS actualMemory,
    average(\`memory-available\`) AS availableMemory,
    average(cpuPercent) AS cpuPercent,
    average(diskUsedPercent) AS diskUsedPercent,
    (average(memoryUsedBytes)/average(memoryTotalBytes))*100 AS memoryUsedPercent,
    latest(domainID) AS domain,
    latest(projectName) AS project
  FROM SystemSample
  FACET entityName
  WHERE entityName NOT LIKE '%\${lookup%'
  LIMIT MAX`.replace(/\s+/g, ' ');

const hypervisors = `SELECT
    latest(entityGuid) AS entityGuid,
    average(openstack.nova.hypervisor.local_gb_used / openstack.nova.hypervisor.local_gb) * 100 AS diskUsedPct,
    average(openstack.nova.hypervisor.memory_mb_used / openstack.nova.hypervisor.memory_mb) * 100 AS memoryUsedPct,
    average(openstack.nova.hypervisor.running_vms) AS runningVMs,
    average(openstack.nova.hypervisor.vcpus_used) AS usedVCPUs,
    average(openstack.nova.hypervisor.memory_mb) AS totalMemory,
    average(openstack.nova.hypervisor.free_ram_mb) AS availableMemory,
    average(openstack.nova.hypervisor.load_average_1) AS cpuPercent1Minute,
    average(openstack.nova.hypervisor.load_average_5) AS cpuPercent5Minute,
    average(openstack.nova.hypervisor.load_average_15) AS cpuPercent15Minute,
    average(openstack.nova.hypervisor.local_gb_used / openstack.nova.hypervisor.local_gb) * 100 AS diskUsedPercent,
    average(openstack.nova.hypervisor.memory_mb_used / openstack.nova.hypervisor.memory_mb) * 100 AS diskUsedPercent,
    latest(openstack.domain.id) AS domain
  FROM OSHypervisorSample
  FACET openstack.nova.hypervisor.hypervisor_hostname, openstack.nova.hypervisor.id
  LIMIT MAX`.replace(/\s+/g, ' ');

const servers = `SELECT
    latest(entityGuid) AS entityGuid,
		average(\`openstack.nova.server.memory-actual\`) AS actualMemory,
		average(\`openstack.nova.server.memory-available\`) AS availableMemory,
		average((\`openstack.nova.server.memory-actual\` - \`openstack.nova.server.memory-available\`) / \`openstack.nova.server.memory-actual\`) * 100 AS memoryUsedPct,
		average(\`openstack.nova.server.memory-rss\`) AS rssMemory,
		average(\`openstack.nova.server.memory-unused\`) AS unusedMemory,
		average(\`openstack.nova.server.memory-usable\`) AS usableMemory,
		latest(openstack.project.id) AS projectId,
		latest(openstack.project.name) AS projectName,
		latest(openstack.domain.id) AS domain,
    latest(openstack.nova.server.hypervisor_name) AS hypervisorName
  FROM OSServerSample
  FACET openstack.nova.server.name, openstack.nova.server.id
  LIMIT MAX`.replace(/\s+/g, ' ');

const nova = `SELECT
    latest(openstack.compute.agents_count) AS agents,
    latest(openstack.compute.aggregates_count) AS aggregates,
    latest(openstack.compute.flavors_count) AS flavors,
    latest(openstack.compute.keypairs_count) AS keypairs,
    latest(openstack.compute.services_count) AS services
  FROM OSNovaSample
  FACET openstack.domain.id
  LIMIT MAX`.replace(/\s+/g, ' ');

const keystone = `SELECT
    latest(openstack.identity.credentials_count) AS credentials,
    latest(openstack.identity.domains_count) AS domains,
    latest(openstack.identity.groups_count) AS groups,
    latest(openstack.identity.policies_count) AS policies,
    latest(openstack.identity.projects_count) AS projects,
    latest(openstack.identity.regions_count) AS regions,
    latest(openstack.identity.roles_count) AS roles,
    latest(openstack.identity.services_count) AS services,
    latest(openstack.identity.users_count) AS users
  FROM OSKeystoneSample
  FACET openstack.domain.id
  LIMIT MAX`.replace(/\s+/g, ' ');

exports.graphql = `{
  actor {
    account(id: ${accountId}) {
      hypervisors: nrql(query: "${hypervisors}") {
        results
      }
      servers: nrql(query: "${servers}") {
        results
      }
      nova: nrql(query: "${nova}") {
        results
      }
      keystone: nrql(query: "${keystone}") {
        results
      }
    }
    appEntities: entitySearch(queryBuilder: {domain: APM}) {
      results {
        entities {
          guid
          name
          tags {
            key
            values
          }
          ... on ApmApplicationEntityOutline {
            reporting
            alertSeverity
          }
        }
      }
    }
    dashboards: entitySearch(queryBuilder: {type: DASHBOARD}) {
      results {
        entities {
          name
          guid
        }
      }
    }
    hostEntities: entitySearch(queryBuilder: {domain: INFRA, type: HOST}) {
      results {
        entities {
          ... on InfrastructureHostEntityOutline {
            guid
            name
            reporting
            alertSeverity
            hostSummary {
              cpuUtilizationPercent
              diskUsedPercent
              memoryUsedPercent
            }
          }
        }
      }
    }
  }
}`;
