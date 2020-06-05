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
      nrql: nrql(query: "${nrql}") {
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
