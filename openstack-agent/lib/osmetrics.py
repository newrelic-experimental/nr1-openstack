import sys
import re
import json
import logging
import osutils


logger = logging.getLogger("nr.os.mon.metrics")
# ==========================================
class ProcessMetrics:

  # ----------------------------------------
  def __init__(self, os_auth, config, file_handles, service_type):
    self.os_auth = os_auth
    self.config = config
    self.file_handles = file_handles
    self.service_type = service_type
    self.current_project = {}


  # ----------------------------------------
  def write_result(self, fh, message):
    # write metrics to outfile files
    logger.log(logging.DEBUG, "in write_result: " + str(fh))
    fh.write(message + "\n")
    fh.flush()


  # ----------------------------------------
  def close_output_files(self):
    for fh in self.file_handles:
      logger.log(logging.DEBUG, "closing output channel for %s " + str(fh))
      self.file_handles[fh].flush()
      self.file_handles[fh].close()


  # ----------------------------------------
  def getServerMetrics(self, project):
    # get server metrics for the "project"
    token = project["auth_token"]
    svc = "compute"
    endpoint = "/servers"
    resp = self.os_auth.iterate_endpoint_interfaces(project["catalog"], svc, endpoint, token)
    if not resp:
      logger.log(logging.WARNING, "skipping server metrics collection - could not find valid compute endpoint")
      return

    for server in resp.get("servers"):
      logger.log(logging.DEBUG, "server id: %s --- server name: %s", server.get("id"), server.get("name"))
      endpoint = "/servers/{0}/diagnostics".format(server.get("id"))
      resp = self.os_auth.iterate_endpoint_interfaces(project["catalog"], svc, endpoint, token)
      if not resp:
        logger.log(logging.WARNING, "skipping server metrics collection for server %s (%s) - could not find valid compute endpoint", server.get("id"), server.get("name"))
        return
      resp['id'] = server.get("id")
      resp['name'] = server.get("name")

      keys = resp.keys()
      for key in keys:
        match = re.match('^.*_([rt]x.*)$', key)
        if match:
          resp[match.group(1)] = resp[key]
          del resp[key]

      metrics = '{"server": ' + json.dumps(resp) + ' }'

      self.write_result(
        self.file_handles["servers"], 
        self.constructInsightsEvent("servers", "project", metrics)
      )


  # ----------------------------------------
  def getProjectLimits(self, project):
    # get "project"  limits
    token = project["auth_token"]
    svc = "compute"
    endpoint = "/limits"
    resp = self.os_auth.iterate_endpoint_interfaces(project["catalog"], svc, endpoint, token)
    if not resp:
      logger.log(logging.WARNING, "skipping project limits collection - could not find valid compute endpoint")
      return

    metrics = '{"limits": ' + json.dumps(resp['limits']['absolute']) + ' }'

    self.write_result(
      self.file_handles["limits"], 
      self.constructInsightsEvent("limits", "project", metrics)
    )


  # ----------------------------------------
  def getBlockStorageMetrics(self, project):
    # get block storage metrics for the "project"

    # get limits for block storage (cinder)
    token = project["auth_token"]
    svc = "block-storage"
    endpoint = "/limits"

    cinder_limits = self.os_auth.iterate_endpoint_interfaces(project["catalog"], svc, endpoint, token)
    if not cinder_limits:
      logger.log(logging.WARNING, "skipping block storage limits collection - could not find valid block_storage endpoint")
      return
    # get snapshot metrics for block storage (cinder)
    endpoint = "/snapshots"
    cinder_snapshots = self.os_auth.iterate_endpoint_interfaces(project["catalog"], svc, endpoint, token)
    if not cinder_snapshots:
      logger.log(logging.WARNING, "skipping block storage snapshots collection - could not find valid block_storage endpoint")
      return
    snapshot_length = len(cinder_snapshots['snapshots'])
    size = 0
    for snapshot in cinder_snapshots['snapshots']:
      size = size + snapshot['size']
    # get volume metrics for block storage (cinder)
    endpoint = "/volumes/detail"
    cinder_volumes = self.os_auth.iterate_endpoint_interfaces(project["catalog"], svc, endpoint, token)
    if not cinder_volumes:
      logger.log(logging.WARNING, "skipping block storage volumes collection - could not find valid block_storage endpoint")
      return
    volumes_length = len(cinder_volumes['volumes'])
    size = 0
    for volume in cinder_volumes['volumes']:
      size = size + volume['size']

    metrics = '{"limits": ' + json.dumps(cinder_limits['limits']['absolute']) + \
        ', "snapshots": { "count": ' + str(snapshot_length) + ', "size": ' + str(size) + ' }' + \
        ', "volumes": { "count": ' + str(volumes_length) + ', "size": ' + str(size) + ' } }'

    self.write_result(
      self.file_handles["block_storage"], 
      self.constructInsightsEvent("block_storage", "project", metrics)
    )


  # ----------------------------------------
  def getHypervisorMetrics(self, service):
    url = "{0}/os-hypervisors".format(service["catalog"]["nova"]["public"]["url"])
    # get list of hypervisors
    token = service["auth_token"]
    svc = "compute"
    endpoint = "/os-hypervisors"

    resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
    if not resp:
      logger.log(logging.WARNING, "skipping hypervisor collection - could not find valid compute endpoint")
      return
    logger.log(logging.DEBUG, "hypervisors: %s", json.dumps(resp, sort_keys=True, indent=2, separators=(',', ': ')))
    for hypervisor in resp.get("hypervisors"):
      logger.log(logging.DEBUG, "hypervisor id: %s", hypervisor.get("id"))
      # collect metrics for hypervisors
      endpoint = "/os-hypervisors/{0}".format(hypervisor.get("id"))
      hypervisor_metrics = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
      if not hypervisor_metrics:
        logger.log(logging.WARNING, "skipping hypervisor metrics collection - could not find valid compute endpoint")
        return
      logger.log(logging.DEBUG, "hypervisor %s: %s", hypervisor.get("id"), json.dumps(hypervisor_metrics, sort_keys=True, indent=2, separators=(',', ': ')))

      # get uptime
      endpoint = "{0}/uptime".format(endpoint)
      hypervisor_uptime = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
      if not hypervisor_uptime:
        logger.log(logging.WARNING, "skipping hypervisor uptime collection - could not find valid compute endpoint")
      else:
        logger.log(logging.DEBUG, "hypervisor uptime: %s", hypervisor_uptime["hypervisor"]["uptime"])
        uptime_array = hypervisor_uptime["hypervisor"]["uptime"].split(",")
        hours = minutes = 0
        if len(uptime_array) == 6:
          ### ex. [' 22:28:49 up 1 day', '  3:56', '  2 users', '  load average: 0.99', ' 1.02', ' 1.00\n']
          ### ex. [' 22:28:49 up 1 day', ' 31 min', '  2 users', '  load average: 0.99', ' 1.02', ' 1.00\n'] ## midnight
          days = uptime_array[0].strip().split(" ")[2]
          tmp_str1 = uptime_array[1].strip().split(":")
          if len(tmp_str1) == 1:
            hours = 0
            minutes = tmp_str1[0]
          else:
            hours = tmp_str1[0]
            minutes = tmp_str1[1]
          up_since =  "{0} days, {1} hours, {2} minutes".format(days, hours, minutes)
          users = uptime_array[2].strip()[0]
        else:
          ### ex. [' 19:46:40 up  1:14', '00:1 user', '  load average: 0.16', ' 0.07', ' 0.10\n']
          tmp_str1 = uptime_array[0].strip().replace("  ", " ").split(" ")[2].split(":")
          hours = tmp_str1[0]
          minutes = tmp_str1[1]
          up_since =  "{0} days, {1} hours, {2} minutes".format(days, hours, minutes)
          users = uptime_array[1].replace("00:", "").strip().split(" ")[0]

        hypervisor_metrics["hypervisor"]["uptime"] = up_since
        hypervisor_metrics["hypervisor"]["user_count"] = int(users)
        hypervisor_metrics["hypervisor"]["load_average_1"] = float(uptime_array[-3].strip().split(" ")[2])
        hypervisor_metrics["hypervisor"]["load_average_5"] = float(uptime_array[-2].strip().split(" ")[0])
        hypervisor_metrics["hypervisor"]["load_average_15"] = float(uptime_array[-1].strip().split(" ")[0])
      ### ------------------------------------------------------------------

      del hypervisor_metrics["hypervisor"]["cpu_info"]

      metrics = json.dumps(hypervisor_metrics)

      self.write_result(
        self.file_handles["hypervisors"], 
        self.constructInsightsEvent("hypervisors", "system", metrics)
      )


  # ----------------------------------------
  def getNetworkResourceCount(self, service, resource):
    # get count for resources: "routers", "subnets", "floatingips", "security-groups"
    token = service["auth_token"]
    svc = "network"
    endpoint = "/{0}/{1}".format(service["neutron_api_version"], resource)
    resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
    if not resp:
      logger.log(logging.WARNING, "skipping network resource count collection - could not find valid network endpoint")
      return
    # logger.log(logging.DEBUG, "%s: %s", resource, json.dumps(resp, sort_keys=True, indent=2, separators=(',', ': ')))
    resource_count = len(resp[resource.replace("-", "_")])
    logger.log(logging.DEBUG, "%s count: %d", resource, resource_count)

    return resource_count


  # ----------------------------------------
  def getNetworkMetrics(self, service):
    # get list of networks
    token = service["auth_token"]
    svc = "network"
    endpoint = "/{0}/networks".format(service["neutron_api_version"])
    resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
    if not resp:
      logger.log(logging.WARNING, "skipping network collection - could not find valid network endpoint")
      return
    logger.log(logging.DEBUG, "networks: %s", json.dumps(resp))
    for network in resp.get("networks"):
      logger.log(logging.DEBUG, "processing network id: %s --- network name: %s", network.get("id"), network.get("name"))
      endpoint = "/{0}/networks/{1}".format(service["neutron_api_version"], network.get("id"))
      network_metrics = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
      if not resp:
        logger.log(logging.WARNING, "skipping network metrics collection - could not find valid network endpoint")
        return
      del network_metrics["network"]["subnets"]
      del network_metrics["network"]["availability_zones"]
      del network_metrics["network"]["availability_zone_hints"]
      del network_metrics["network"]["tags"]

      metrics = json.dumps(network_metrics)

      self.write_result(
        self.file_handles["networks"],
        self.constructInsightsEvent("networks", "system", metrics)
      )


  # ----------------------------------------
  def getGlanceMetrics(self, service):
    # service_type = "glance"

    token = service["auth_token"]
    svc = "image"
    endpoint = "/{0}/images".format(self.config["glance_api_version"])

    resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
    if not resp:
      logger.log(logging.WARNING, "skipping image metrics collection - could not find valid image endpoint")
      return
    logger.log(logging.DEBUG, ">>>> %s%s: %s", svc, endpoint, json.dumps(resp, sort_keys=True, indent=2, separators=(',', ': ')))
    for image in resp.get("images"):
      metrics = '{"image": ' + json.dumps(image) + ' }'

      self.write_result(
        self.file_handles["images"],
        self.constructInsightsEvent("images", "system", metrics)
      )


  # ----------------------------------------
  def getPlacementMetrics(self, service):
    # service_type = "placement"
    token = service["auth_token"]
    svc = "placement"
    endpoint = "/resource_providers"

    resource_providers = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
    if not resource_providers:
      logger.log(logging.WARNING, "skipping placement collection - could not find valid placement endpoint")
      return
    logger.log(logging.DEBUG, ">> %s%s: %s", svc, endpoint, json.dumps(resource_providers, sort_keys=True, indent=2, separators=(',', ': ')))
    for resource_provider in resource_providers.get("resource_providers"):
      logger.log(logging.DEBUG, ">> resource provider: %s", json.dumps(resource_provider, sort_keys=True, indent=2, separators=(',', ': ')))
      endpoint = "/resource_providers/{0}/inventories".format(resource_provider["uuid"])
      inventory_resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
      if not inventory_resp:
        logger.log(logging.WARNING, "skipping placement inventory collection - could not find valid placement endpoint")
        return
      logger.log(logging.DEBUG, ">> respource provider inventories: %s", json.dumps(inventory_resp, sort_keys=True, indent=2, separators=(',', ': ')))

      endpoint = "/resource_providers/{0}/usages".format(resource_provider["uuid"])
      usage_resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], svc, endpoint, token)
      if not usage_resp:
        logger.log(logging.WARNING, "skipping placement usages collection - could not find valid placement endpoint")
        return
      logger.log(logging.DEBUG, ">> respource provider usages: %s", json.dumps(usage_resp, sort_keys=True, indent=2, separators=(',', ': ')))

      metrics = '{"resource": {"name": "' + resource_provider["name"] + '", "uuid": "' + \
        resource_provider["uuid"] + '"}, "inventories": ' + json.dumps(inventory_resp["inventories"]) + \
        ', "resource_provider_generation": ' + str(inventory_resp["resource_provider_generation"]) + \
        ', "usages": ' + json.dumps(usage_resp["usages"]) + ' }'

      self.write_result(
        self.file_handles["resource_providers"],
        self.constructInsightsEvent("resource_providers", "system", metrics)
      )


  # -----------------------------------------------------------
  def constructInsightsEvent(self, service_type, resource, ev):

    # ---------------------------------------------------------
    def traverseEvent(ev, key="", isList=False):

      if type(ev) is dict:
        for k, v in ev.items():
          traverseEvent(v, key+k+".", isList)
        
      elif type(ev) is list:
          c = 0
          isList = True
          for el in ev:                 
            traverseEvent(el, key[:-1]+"_"+str(c)+".", isList) 
            c += 1
      else:
        element = "openstack.{0}.{1}".format(component_name, key[:-1])
        if element in metric_names or (isList and add_lists):
          # print(element, ": ", ev)
          event[element] = ev


    ev = json.loads(ev)
    # print("raw metrics for {0}: {1}".format(service_type, json.dumps(ev, sort_keys=True, indent=2, separators=(',', ': '))))
    metric_names = self.config["service_types"][service_type]["metrics"]
    component_name = self.config["service_types"][service_type]["component_name"]
    add_lists = False
    if "add_lists" in self.config:
      add_lists = self.config["add_lists"]
    event = {}
    traverseEvent(ev)
    event["openstack.domain.id"] = "default"
    if resource == "project":
      event["openstack.project.id"] = self.current_project["id"]
      event["openstack.project.name"] = self.current_project["name"]
    
    return json.dumps(event)


  # ----------------------------------------
  def getSystemCounts(self, service, service_type, endpoints):

    resource_metrics = {}
    token = service["auth_token"]
    for ep in endpoints:

      resp = None
      if service_type == "identity":
        ep = "/{0}{1}".format(self.config["keystone_api_version"], ep)
      try:
        resp = self.os_auth.iterate_endpoint_interfaces(service["catalog"], service_type, ep, token)
        if not resp:
          logger.log(logging.WARNING, "skipping system counts collection - could not find valid %s endpoint", service_type)
          return
        logger.log(logging.DEBUG, ">>>> %s: %s", ep, json.dumps(resp))#, sort_keys=True, indent=2, separators=(',', ': ')))

        metricName = ep[ep.rfind("/")+1:]
        if "-" in metricName:
          metricName = metricName[metricName.rfind("-")+1:]
        metric_count = len(resp[metricName])
        resource_metrics["{0}_count".format(metricName)] = metric_count
        logger.log(logging.DEBUG, ">>>> %s count: %d", metricName, metric_count)

      except:
        logger.log(logging.ERROR, ">>>> endpoint: %s", ep)
        logger.log(logging.ERROR, ">>>> line#: %s", sys.exc_info()[-1].tb_lineno)
        logger.log(logging.ERROR, ">>>> error message: %s", sys.exc_info())
        logger.log(logging.ERROR, ">>>> response body: %s", json.dumps(resp))

    for resource in ["routers", "subnets", "floatingips", "security-groups"]:
      resource_count = self.getNetworkResourceCount(service, resource)
      resource_metrics["{0}_count".format(resource.replace("-", "_"))] = resource_count

    metrics = json.dumps(resource_metrics)

    return metrics


  # ----------------------------------------
  def getSystemMetrics(self):
    # get metrics for system, nova resource counts, hypervisors, networks, glance, placement
    service = self.os_auth.getSystemAuth(self.config)
    logger.log(logging.DEBUG, ">>> SERVICES: %s", json.dumps(service, sort_keys=True, indent=2, separators=(',', ': ')))

    # keystone metrics
    if (self.service_type == "all" or self.service_type == "keystone") and self.config["service_types"]["keystone"]["enabled"]:
      logger.log(logging.INFO, ">>> collecting keystone count metrics")
      keystone_endpoints = [
        "/auth/projects",
        "/users",
        "/services",
        "/policies",
        "/domains",
        "/groups",
        "/regions",
        "/credentials",
        "/roles"
      ]
      metrics = self.getSystemCounts(service, "identity", keystone_endpoints)


      if metrics:
        self.write_result(
          self.file_handles["keystone"],
          self.constructInsightsEvent("keystone", "system", metrics)
        )

    #nova resource counts
    if (self.service_type == "all" or self.service_type == "nova") and self.config["service_types"]["nova"]["enabled"]:
      logger.log(logging.INFO, ">>> collecting nova count metrics")
      nova_endpoints = [
        "/os-keypairs",
        "/os-agents",
        "/os-services",
        "/flavors",
        "/os-aggregates"
      ]
      metrics = self.getSystemCounts(service, "compute", nova_endpoints)
      if metrics:
        self.write_result(
          self.file_handles["nova"],
          self.constructInsightsEvent("nova", "system", metrics)
        )

    # hypervisors
    if (self.service_type == "all" or self.service_type == "hypervisors") and self.config["service_types"]["hypervisors"]["enabled"]:
      logger.log(logging.INFO, ">>> collecting hypervisors metrics")
      self.getHypervisorMetrics(service)

    # networks
    if (self.service_type == "all" or self.service_type == "networks") and self.config["service_types"]["networks"]["enabled"]:
      logger.log(logging.INFO, ">>> collecting networks metrics")
      self.getNetworkMetrics(service)

    # glance
    if (self.service_type == "all" or self.service_type == "images") and self.config["service_types"]["images"]["enabled"]:
      logger.log(logging.INFO, ">>> collecting image data")
      self.getGlanceMetrics(service)

    # placement
    if (self.service_type == "all" or self.service_type == "resource_providers") and self.config["service_types"]["resource_providers"]["enabled"]:
      logger.log(logging.INFO, ">>> collecting resource providers' inventory and usage")
      self.getPlacementMetrics(service)


  # ----------------------------------------
  def getProjectMetrics(self):
    # get user token
    identity = self.os_auth.getIdentity("user") # get auth for user
    auth_scope = "unscoped"
    keystone_token_url = osutils.getKeystoneTokensUrl(self.config)
    resp = self.os_auth.getAuthToken(keystone_token_url, auth_scope, identity) # unscoped
    if not resp:
      sys.exit("Unable to obtain user token. Terminating the process\n")

    os_user_auth_token = resp.info().getheader('X-Subject-Token')

    # # get project list
    keystone_project_url = osutils.getKeystoneProjectsUrl(self.config)
    resp = self.os_auth.os_request(keystone_project_url, os_user_auth_token)
    logger.log(logging.DEBUG, ">>>> PROJECTS: %s", json.dumps(resp.get("projects"), sort_keys=True, indent=2, separators=(',', ': ')))


    # get server, limits, and block storage metrics for the "project"
    for project in resp.get("projects"):
      self.os_auth.getProjectAuth(self.config, project, os_user_auth_token)
      logger.log(logging.DEBUG, ">>> PROJECT %s: %s", project["name"], json.dumps(project, sort_keys=True, indent=2, separators=(',', ': ')))
      self.current_project = project

      # project servers
      if (self.service_type == "all" or self.service_type == "servers") and self.config["service_types"]["servers"]["enabled"]:
        logger.log(logging.INFO, ">>> collecting server metrics for project %s", project["name"])
        self.getServerMetrics(project)

      # project limits
      if (self.service_type == "all" or self.service_type == "limits") and self.config["service_types"]["limits"]["enabled"]:
        logger.log(logging.INFO, ">>> collecting limits for project %s", project["name"])
        self.getProjectLimits(project)

      # project block storage
      if (self.service_type == "all" or self.service_type == "block_storage") and self.config["service_types"]["block_storage"]["enabled"]:
        logger.log(logging.INFO, ">>> collecting block storage limits for project %s", project["name"])
        self.getBlockStorageMetrics(project)

