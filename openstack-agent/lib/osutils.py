import sys
import os
import re
import urlparse
import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler


# ==========================================
# -----------------------------------------------------------
# -----------------------------------------------------------

def setLogging(config):
  log_settings = config.get("logging")

  logDir = os.path.join(str(config.get("nr_agent_home")), "logs")
  if not os.path.exists(logDir):
    os.makedirs(logDir)

  logger = logging.getLogger(log_settings.get("logger_name"))

  switcher = {
      "DEBUG": logging.DEBUG,
      "INFO": logging.INFO,
      "WARNING": logging.WARNING,
      "ERROR": logging.ERROR,
      "CRITICAL": logging.CRITICAL
  }
  logger.setLevel(switcher.get(log_settings.get("log_level"), logging.INFO))

  file_handler = TimedRotatingFileHandler(os.path.join(logDir, str(log_settings.get("log_file_name"))), when='midnight', interval=1, backupCount=7)
  file_handler.setFormatter(logging.Formatter(str(log_settings.get("formatter"))))
  logger.addHandler(file_handler)
  if sys.stdin.isatty():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_settings.get("formatter")))
    logger.addHandler(console_handler)

  logger.propagate = False

  if str(log_settings.get("log_level")) == "DEBUG":
    logger.log(logging.INFO, "log level set to DEBUG...")

  logger.log(logging.INFO, ">>> executing from terminal: %s", str(sys.stdin.isatty()))

  return logger

def updateUrlApiVersion(config, url, os_service=None):
  # update url api version for service:interface if specified in config
  svc_api_version_property_name = "{0}_api_version".format(os_service)
  if svc_api_version_property_name in config:
    parsed_url = list(urlparse.urlparse(url))
    if len(parsed_url[2]):
      regex = "(\\/)([vV]{1}[0-9]+)(\\.?[0-9]*)(\\/|$)"
      repl = "\\1{0}\\4".format(config[svc_api_version_property_name])
      parsed_url[2] = re.sub(regex, repl, parsed_url[2])
      url = urlparse.urlunparse(parsed_url)

  return getOsUrl(config, url)


def getOsUrl(config, url):
  if "alternate_host" not in config:
    return url

  parsed_url = list(urlparse.urlparse(url))
  if parsed_url[1]:
    split = parsed_url[1].split(':')
    if len(split) == 1:
      parsed_url[1] = config['alternate_host']
    else:
      parsed_url[1] = config['alternate_host'] + ':' + split[1]
    return urlparse.urlunparse(parsed_url)

  return url

def getKeystoneTokensUrl(config):
  return getOsUrl(
    config,
    config["keystone_url"] + "/" + config["keystone_api_version"] + "/auth/tokens",
  )

def getKeystoneProjectsUrl(config):
  return getOsUrl(
    config,
    config["keystone_url"] + "/" + config["keystone_api_version"] + "/auth/projects",
  )


