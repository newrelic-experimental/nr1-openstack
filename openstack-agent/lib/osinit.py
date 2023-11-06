import sys
import argparse
import os
import time
import json


# ==========================================
class InvalidConfig(Exception):
    pass

# ==========================================
class OpenStackInit:
  # ----------------------------------------
  def __init__(self):

    parser = argparse.ArgumentParser(description='Parser')
    parser.add_argument("-c", "--config", "--config_file", "--configFile", type=str)
    parser.add_argument("-s", "--service", "--service_type", "--serviceType",
      choices=["servers", "limits", "block_storage", "networks", "hypervisors", "keystone", "nova", "resource_providers", "images"],
      type=str, default="all")

    args = parser.parse_args()

    cfgFileName = args.config
    self.serviceType = args.service


    try:
      # print("command: ", sys.argv[0], len(sys.argv))
      if cfgFileName == None:
        path = sys.argv[0]
        p1 = path.rfind("/")
        if p1 > -1:
          cfgFileName = os.path.join(path[0:p1], "config", "os-config.json")
        else:
          cfgFileName = os.path.join(".", "config", "os-config.json")

        if not os.path.exists(cfgFileName):
          cfgFileName = os.path.join(".", "os-config.json")


      with open(cfgFileName, "r") as configFile:
        self.os_config = json.load(configFile)


    except OSError as err:
      print("\tcan't read config file. either specify config file's full name in command line,")
      print("\tor make sure it exists in config folder of the agent installation directory,")
      print("\tand verify the content.\n")
      sys.exit("I/O error({0})".format(err))

    try:
      serviceTypesFileName = os.path.join(
        os.path.dirname(__file__),
        "service-types.json"
      )

      with open(serviceTypesFileName, "r") as serviceTypesFile:
        service_types = json.load(serviceTypesFile)
        if not service_types['all_types_by_service_type']:
          print("invalid service-types.json\n")
          sys.exit("Invalid Service Types")
        self.service_types = service_types['all_types_by_service_type']
    except OSError as err:
      print("\tmissing service-types.json\n")
      sys.exit("I/O error({0})".format(err))

    if not "nr_agent_home" in self.os_config["config"] or self.os_config["config"]["nr_agent_home"] == "":
      print("\tnr_agent_home not set in config file. seting agent home to current directory\n")
      self.os_config.get("config")["nr_agent_home"] = cfgFileName[0:cfgFileName.rfind("/")] # "."



    try:
      if not self.os_config.get("config").get("keystone_url"):
        raise InvalidConfig()
    except InvalidConfig:
      print("keystone_url missing from config\n")
      sys.exit("Exiting 2\007\n")


    try:
      if not self.os_config.get("config").get("keystone_api_version"):
        raise InvalidConfig()
    except InvalidConfig:
      print("keystone_api_version missing from config\n")
      sys.exit("Exiting 3\007\n")


    user = self.os_config.get("config").get("user")
    try:
      if not (user and user.get("name") and user.get("password")
          and user.get("domain") and user.get("domain").get("id")):
          raise InvalidConfig()

    except InvalidConfig:
      print("user identity missing or misconfigured in config\n")
      sys.exit("Exiting 4\007\n")



  # ----------------------------------------
  def getConfig(self):

    return self.os_config["config"]



  # ----------------------------------------
  def getFileHandles(self):

    return self.os_config["output_file_handles"]

  # ----------------------------------------
  def getServiceTypes(self):

    return self.service_types

  # ----------------------------------------
  def createDirectory(self, dir):
    if not os.path.exists(dir):
      os.makedirs(dir)



  # ----------------------------------------
  def createOutPutFile(self, outfile):
    return open(outfile, "a")



  # ----------------------------------------
  def prepareEnvironment(self):
    timestamp = int(round(time.time() * 1000))
    output_file_handles = {}
    for service_type, service in list(self.os_config.get("config").get("service_types").items()):
      if (service_type == self.serviceType or self.serviceType == "all") and service["enabled"]:
        dir = os.path.join(self.os_config.get("config").get("nr_agent_home"), "data", service_type)
        self.createDirectory(dir)
        outfile = os.path.join(dir, "{0}_{1}.json".format(service_type, timestamp))
        output_file_handles[service_type] = self.createOutPutFile(outfile)

    self.os_config["output_file_handles"] = output_file_handles

