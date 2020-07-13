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
        memoryUsedPercent: (cur.hostSummary || {}).memoryUsedPercent,
      },
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
            alertSeverity: cur.alertSeverity,
          });
        });
    });
    return acc;
  }, {});

  const dataObj = { hosts: {}, domains: {} };

  dataObj.hypervisors = (
    ((actor.account || {}).hypervisors || {}).results || []
  ).reduce((acc, cur) => {
    acc[cur.facet[0]] = {
      availableMemory: cur.availableMemory,
      cpuPercent1Minute: cur.cpuPercent1Minute,
      cpuPercent5Minute: cur.cpuPercent5Minute,
      cpuPercent15Minute: cur.cpuPercent15Minute,
      diskUsedPct: cur.diskUsedPct,
      diskUsedPercent: cur.diskUsedPercent,
      domain: cur.domain,
      memoryUsedPct: cur.memoryUsedPct,
      runningVMs: cur.runningVMs,
      totalMemory: cur.totalMemory,
      usedVCPUs: cur.usedVCPUs,
      name: cur.facet[1],
      guid: null,
      host: cur.facet[0],
      alertSeverity: null,
      reporting: null,
      servers: [],
    };
    return acc;
  }, {});

  (((actor.account || {}).servers || {}).results || []).map(server => {
    const hypervisor = server.hypervisorName;
    const serverName = server.facet[0];
    const domain = server.domain;
    const project = server.projectName;
    const serverObj = {
      name: serverName,
      fullName: serverName,
      apps: serverName in serverApps ? serverApps[serverName] : [],
      actualMemory: server.actualMemory,
      availableMemory: server.availableMemory,
      memoryUsedPct: server.memoryUsedPct,
      projectId: server.projectId,
      projectName: project,
      domain: domain,
      rssMemory: server.rssMemory,
      unusedMemory: server.unusedMemory,
      usableMemory: server.usableMemory,
      guid: null,
      reporting: null,
      alertSeverity: null,
    };

    if (hypervisor in dataObj.hypervisors)
      dataObj.hypervisors[hypervisor].servers.push(serverObj);
    if (domain) {
      if (!(domain in dataObj.domains)) dataObj.domains[domain] = {};
      if (project) {
        if (!(project in dataObj.domains[domain]))
          dataObj.domains[domain][project] = [];
        dataObj.domains[domain][project].push(serverObj);
      }
    }
  });

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
        services: cur.services,
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
      users: cur.users,
    };
    return acc;
  }, {});

  return dataObj;
};
