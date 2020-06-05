import sys
import json
import logging
import urllib2
from lib import osutils

logger = logging.getLogger("nr.os.mon.auth")
# ==========================================
class OpenStackAuth:

  # ----------------------------------------
  def __init__(self, config, service_types):
    logger.log(logging.DEBUG, "initialize OpenStackAuth")
    self.user = config["user"]["name"]
    self.password = config["user"]["password"]
    self.domain = config["user"]["domain"]["id"]

    self.service_types = service_types

    self.user_auth_token = ""
    self.last_project = {}


  # ----------------------------------------
  def getIdentity(self, scope, token=None):
    # return {"auth": {"identity": {"user": {"name": self.user, "password": self.password, "domain": {"id": self.domain} } }
    logger.log(logging.DEBUG, "create %s identity", scope)
    if scope in ["user", "system"]:
      return {
        "methods": ["password"],
        "password": {
          "user": {
            "name": self.user,
            "password": self.password,
            "domain": {
              "id": self.domain
            }
          }
        }
      }
    else:
      return {
        "methods": ["token"],
        "token": {
          "id": token
        }
      }


  # ----------------------------------------
  def getAuthToken(self, url, auth_scope, identity, ssl_verify=False):
    logger.log(logging.DEBUG, "fetch auth token")
    if not auth_scope:
        auth_scope = "unscoped"

    payload = {"auth": {"identity": identity, "scope": auth_scope}}

    headers = {"Content-Type": "application/json"}

    try:
      req = urllib2.Request(
        url,
        data=json.dumps(payload),
        headers=headers,
      )
      resp = urllib2.urlopen(req)

      if auth_scope == "unscoped":
        self.user_auth_token = resp.info().getheader('X-Subject-Token')

    except urllib2.HTTPError as e:
      logger.log(logging.CRITICAL, "Error @ line %s", str(sys.exc_info()[2].tb_lineno))
      if hasattr(e, 'reason'):
        logger.log(logging.ERROR, "Failed to connect to endpoint: %s...", url)
        logger.log(logging.ERROR, "Reason: %s", e.reason)
      if hasattr(e, 'code'):
        logger.log(logging.ERROR, "Http status code: %s", e.code)
      logger.log(logging.CRITICAL, "auth scope identity: %s", json.dumps(auth_scope))
      logger.log(logging.ERROR, "response body: %s", e.read())
      return False

    return resp


  # ----------------------------------------
  def os_request(self, url, token, ssl_verify=False):
    logger.log(logging.DEBUG, "make REST API request -- url:  %s", url)
    logger.log(logging.DEBUG, "token:  %s", token)
    headers = {
      "Content-Type": "application/json",
      "X-Auth-Token": token
    }

    try:
      req = urllib2.Request(
        url,
        headers=headers,
      )
      resp = urllib2.urlopen(req)

    except urllib2.HTTPError as e:
      logger.log(logging.CRITICAL, "Error @ line %s", str(sys.exc_info()[2].tb_lineno))
      if hasattr(e, 'reason'):
        logger.log(logging.ERROR, "Failed to connect to endpoint: %s...", url)
        logger.log(logging.ERROR, "Reason: %s", e.reason)
      if hasattr(e, 'code'):
        logger.log(logging.ERROR, "Http status code: %s", e.code)
      logger.log(logging.ERROR, "response body: %s", e.read())
      # sys.exit("Terminating the process - exit code:e6\007\n")
      return False

    return json.load(resp)

  # ----------------------------------------
  def resolve_service_type(self, catalog, service_type):
    if service_type not in self.service_types:
      return None

    for alias in self.service_types[service_type]:
      # O(M*N) gross I know
      for k, v in catalog.items():
        if v["type"] == alias:
          logger.log(logging.DEBUG, "Found catalog service %s for service type %s using alias %s", k, service_type, alias)
          return v

    return None

  # ----------------------------------------
  def iterate_endpoint_interfaces(self, catalog, service_type, endpoint, token, ssl_verify=False):
    service = self.resolve_service_type(catalog, service_type)
    if not service:
      logger.log(logging.WARNING, "Unable to find a service endpoint in the catalog for service type %s", service_type)
      return None

    for interface in [ "public", "internal", "admin" ]:
      if interface in service:
        url = "{0}{1}".format(service[interface]["url"], endpoint)
        logger.log(logging.DEBUG, "service: %s -- interface: %s -- url/endpoint:  %s", service_type, interface, url)
        resp = self.os_request(url, token)
        if resp:
          return resp

    logger.log(logging.CRITICAL, "cannot connect to any of the service interfaces for \"%s\"", service_type)
    sys.exit("Terminating the process - exit code:e7\007\n")

    return None

  # ----------------------------------------
  def getAuthScope(self, project=None):
    if project: # project auth scope
      logger.log(logging.DEBUG, "get project scope for %s", project["name"])
      return {
        "project": {
          "name": project.get("name"),
          "id": project.get("id"),
          "domain": {
            "id": project.get("domain_id")
          }
        }
      }
    else: # system auth scope
      logger.log(logging.DEBUG, "get system auth scope")
      return {
        "system": {
          "all": True
        }
      }


  # ----------------------------------------
  def setServiceEndpoints(self, config, scope, service_catalog):
    # loop through the catalog to save the service's endpoints for public and internal networks

    logger.log(logging.DEBUG, "setting endpoints for %s", scope)
    catalog = {}
    for cat in service_catalog:
      service_name = cat.get("name")
      c = {}
      catalog[service_name] = c
      c["id"] = cat.get("id")
      c["type"] = cat.get("type")

      for ep in cat.get("endpoints"):
        interface = ep.get("interface")
        catalog[service_name][interface] = {}
        catalog[service_name][interface]["id"] = ep.get("id")
        catalog[service_name][interface]["region"] = ep.get("region")
        catalog[service_name][interface]["region_id"] = ep.get("region_id")
        # updateUrlApiVersion() sets the api version, and calls getOsUrl() to set alternate url
        catalog[service_name][interface]["url"] = osutils.updateUrlApiVersion(config, ep.get("url"), service_name)

    # logger.log(logging.DEBUG, "catalog for %s: %s", scope, json.dumps(catalog, sort_keys=True, indent=2, separators=(',', ': ')))

    return catalog


  # ----------------------------------------
  def getSystemAuth(self, config):

    return {
      "name": "system",
      "auth_token": self.last_project["auth_token"],
      # "auth_scope": auth_scope,
      "user": config["user"],
      "neutron_api_version": config["neutron_api_version"],
      "catalog": self.last_project["catalog"],
      "token_source": self.last_project["name"]
    }


  # ----------------------------------------
  def getProjectAuth(self, config, project, os_user_auth_token):
    identity = self.getIdentity("project", os_user_auth_token)
    auth_scope = self.getAuthScope(project)
    keystone_token_url = osutils.getKeystoneTokensUrl(config)
    resp = self.getAuthToken(keystone_token_url, auth_scope, identity) # project-scoped
    if not resp: #type(resp) == urllib2.HTTPError:
      sys.exit("Unable to obtain project token. Terminating the process\n")

    os_project_scoped_token = resp.headers.get("X-Subject-Token")
    respJson=json.load(resp)

    project["auth_token"] = os_project_scoped_token
    project["auth_scope"] = auth_scope,
    project["catalog"] =  self.setServiceEndpoints(config, project["name"], respJson.get("token").get("catalog"))

    self.last_project = project

