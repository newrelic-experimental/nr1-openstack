exports.data = res => {
  const actor = ((res || {}).data || {}).actor || {};
  const hostEntities = (
    ((actor.hostEntities || {}).results || {}).entities || []
  ).reduce((acc, cur) => {
    if (cur.name.includes('${')) return acc;
    acc[cur.guid] = {
      name: cur.name,
      reporting: cur.reporting,
      alertSeverity: cur.alertSeverity,
      hostSummary: {
        cpuUtilizationPercent: (cur.hostSummary || {}).cpuUtilizationPercent,
        diskUsedPercent: (cur.hostSummary || {}).diskUsedPercent,
        memoryUsedPercent: (cur.hostSummary || {}).memoryUsedPercent
      }
    };
    return acc;
  }, {});

  const serverApps = (
    ((actor.appEntities || {}).results || {}).entities || []
  ).reduce((acc, cur) => {
    if (!('tags' in cur)) return acc;
    const appHosts = cur.tags.filter(tag => tag.key === 'oshost');
    // eslint-disable-next-line array-callback-return
    appHosts.map(tag => {
      if ('values' in tag)
        // eslint-disable-next-line array-callback-return
        tag.values.map(server => {
          if (!(server in acc)) acc[server] = [];
          acc[server].push({
            name: cur.name,
            guid: cur.guid,
            reporting: cur.reporting,
            alertSeverity: cur.alertSeverity
          });
        });
    });
    return acc;
  }, {});

  const dataObj = (((actor.account || {}).nrql || {}).results || []).reduce(
    (acc, cur) => {
      const guid = cur.entityGuid;
      const reporting =
        cur.entityGuid in hostEntities
          ? hostEntities[cur.entityGuid].reporting
          : null;
      const alertSeverity =
        cur.entityGuid in hostEntities
          ? hostEntities[cur.entityGuid].alertSeverity
          : null;

      if (cur.entityName.includes('instance:')) {
        const nameParts = cur.entityName.split(':');
        const hostName = nameParts[1];
        const hypervisorName = nameParts[2];
        const serverName = nameParts[3];

        if (!(hypervisorName in acc.hypervisors))
          acc.hypervisors[hypervisorName] = { servers: [] };

        if (hypervisorName && !serverName) {
          Object.assign(acc.hypervisors[hypervisorName], {
            name: hypervisorName,
            host: hostName,
            fullName: cur.entityName,
            diskUsedPct: cur.diskUsedPct,
            memoryUsedPct: cur.memoryUsedPct,
            runningVMs: cur.runningVMs,
            usedVCPUs: cur.usedVCPUs,
            guid,
            reporting,
            alertSeverity
          });
        }

        if (hypervisorName && serverName) {
          const serverObj = {
            name: serverName,
            fullName: cur.entityName,
            apps: serverName in serverApps ? serverApps[serverName] : [],
            actualMemory: cur.actualMemory,
            availableMemory: cur.availableMemory,
            memoryUsedPct:
              ((cur.actualMemory - cur.availableMemory) / cur.actualMemory) *
              100,
            guid,
            reporting,
            alertSeverity
          };

          acc.hypervisors[hypervisorName].servers.push(serverObj);

          if (!(cur.domain in acc.domains)) acc.domains[cur.domain] = {};
          if (!(cur.project in acc.domains[cur.domain]))
            acc.domains[cur.domain][cur.project] = [];
          acc.domains[cur.domain][cur.project].push(serverObj);
        }
      } else {
        acc.hosts[cur.entityName] = {
          name: cur.entityName,
          cpuPercent: cur.cpuPercent,
          memoryUsedPercent: cur.memoryUsedPercent,
          diskUsedPercent: cur.diskUsedPercent,
          guid,
          reporting,
          alertSeverity
        };
      }
      return acc;
    },
    { hosts: {}, hypervisors: {}, domains: {} }
  );

  dataObj.dashboards = (
    ((actor.dashboards || {}).results || {}).entities || []
  ).filter(dashboard => dashboard.name.includes('OpenStack'));

  dataObj.nova = (((actor.account || {}).nova || {}).results || []).reduce(
    (acc, cur) => {
      acc[cur.facet] = {
        agents: cur.agents,
        aggregates: cur.aggregates,
        flavors: cur.flavors,
        keypairs: cur.keypairs,
        services: cur.services
      };
      return acc;
    },
    {}
  );

  dataObj.keystone = (
    ((actor.account || {}).keystone || {}).results || []
  ).reduce((acc, cur) => {
    acc[cur.facet] = {
      credentials: cur.credentials,
      domains: cur.domains,
      groups: cur.groups,
      policies: cur.policies,
      projects: cur.projects,
      regions: cur.regions,
      roles: cur.roles,
      services: cur.services,
      users: cur.users
    };
    return acc;
  }, {});

  return dataObj;
};
