# New Relic Openstack Integration Agent

This folder contains New Relic Infrastructure Flex integration for OpenStack servers. It works both with devstack and openstack servers, and collects metrics from **"nova"**, **"neutron"**, **"cinder"**, **"glance"**, **"placement"**, and resource counts from **"keystone"** and **"nova"** Openstack services. All metrics collected from these Openstack services are ingested into your Insights account for analysis, visualization, alerting, and trouble shooting.



## Requirements

- This integration requires New Relic Infrastructure agent (NRIA) to be installed on the Openstack server.
- Ensure that you have a working openstack environment
- Ensure that **"python 2"** or higher version is installed



## Installation

Here are the steps for installation and configuration.

* clone this repo on the openstack undercloud (or extract the downloaded **".tgz"** file)

* change directory to the local agent folder 
	```bash
	cd openstack-agent/
	```

* copy **"config/os-config.json.template"** to **"config/os-config.json"** and edit the file
	- set correct value for **"nr_agent_home"** (this would the parent directory of the **"config/"** folder)
	- set correct values for **"keystone_url"**, **"keystone_api_version"**, and **"neutron_api_version"**
	- set correct **"admin user password"**, and **"domain.id"**
	- **Note:** instead of admin user, you can add a new user to openstack with visibility to all modules system-wide, and use that new user instead
	- set the preferred api versions for other Openstack services (e.g. cinder_api_version) **if neccesary**
	- **Note:** the agent iterates through all available interfaces ("public", "internal", "admin") for each service endpoint until it gets valid response, or exhausts all interfaces, in which case it will terminate execution. you only need to set api versions here for services if you'd prefer to use a specific api version, or if the correct api version is different than the one specified in projects' (or system) endpoint catalogs

* copy **"scripts/osmetrics.sh.template"** to **"scripts/osmetrics.sh"** and edit the file
	- change the value of **"NR_AGENT_DIR"** environment variable to the absolute path of NR Openstack agent's installation folder (parent directory of the **"scripts/"** folder)
	- grant **"execute"** permission to **"scripts/osmetrics.sh"** (this script will be invokved by New Relic Infrastructure Agent)
	```bash
	chmod +x scripts/osmetrics.sh
	```

* copy **"ohi-integration/flex-openstack.yaml.template"** to **"ohi-integration/flex-openstack.yaml"** and edit the file
	- under **"variable_store"** stanza in the yaml file set the value for **"nrAgentHome"**  variable to New Relic openstack agent home directory (parent directory of the **"ohi-integration/"** folder)

* copy **"ohi-integration/flex-openstack-system.yaml.template"** to **"ohi-integration/flex-openstack-system.yaml"** and edit the file
	- under **"variable_store"** stanza in the yaml file set the value for **"authUrl"**, **"userDomainID"**, **"username"**, and **"password"**  variables to correct values for your openstack installation




* review the content of **"config/os-config.json"**, **"scripts/osmetrics.sh"**, **"ohi-integration/flex-openstack.yaml"**, and **"ohi-integration/flex-openstack-system.yaml"** files, and make sure all values that you edited are accurate

* you could disable the capture of any resources by setting **"enabled"** to **"flase"** for that resource in **"config/os-config.json"**

* additionally you could remove any of the metrics that you wouldn't want to capture for any of the respurces in **"config/os-config.json"**

* ensure that **"python2"** is installed on the target server (python installation method is dependent on specific linux flavor)

* ensure that you have already installed New Relic Infrastructure agent on the Openstack undercloud server
	```bash
	ps -ef | grep "newrelic-infra" | grep -v grep
	```

* copy **"ohi-integration/flex-openstack.yaml"** and **"ohi-integration/flex-openstack-system.yaml"** files to **"/etc/newrelic-infra/integrations.d/"** (you need root or sudo privileges)
	```bash
	sudo cp ohi-integration/flex-openstack.yaml ohi-integration/flex-openstack-system.yaml /etc/newrelic-infra/integrations.d/
	```

* **Note:** the first time **"os-mon.py"** is invoked by NRIA, it would create all required directory structure for logging and telemetry output

* You don't need to restart NRIA. It automatically picks up the flex integration once you copy the yaml file to **"/etc/newrelic-infra/integrations.d/"**".

* Next you need to verify that data is ingested by New Relic Insights.


## Verify Installation

Once the integration starts sending data to your New Relic Insights account, the following event types get created in Insights:

	- OSBlockStorageSample
	- OSHypervisorSample
	- OSImageSample
	- OSKeystoneSample
	- OSLimitSample
	- OSNetworkSample
	- OSNovaSample
	- OSResourceProviderSample
	- OSServerSample

You can go to Insights **"Data Explorer"** and query the data using the following NRQL:

	```
	select count(*) from OSBlockStorageSample, OSHypervisorSample, OSLimitSample, OSNetworkSample, OSResourceProviderSample, OSServerSample, OSImageSample, OSKeystoneSample, OSNovaSample since 10 minutes ago facet eventType() timeseries
	```

In the repo there are JSON files in the **"keysets"** folder which contain keysets (data dictionary) for the above event types that are ingested from Openstack:

	- OSBlockStorageSample-keyset.json
	- OSHypervisorSample-keyset.json
	- OSImageSample-keyset.json
	- OSKeystoneSample-keyset.json
	- OSLimitSample-keyset.json
	- OSNetworkSample-keyset.json
	- OSNovaSample-keyset.json
	- OSResourceProviderSample-keyset.json
	- OSServerSample-keyset.json

You can view these keysets to see which metrics are captured for each resource type.



## Alerts

Change directory to **"openstack-agent/alerts"**, and execute **create-openstack-policy.sh** by passing **"-k"** command line option with your **admin API key** from the target New Relic account. This will create an alert policy in the account with a number of conditions for the OpenStack enviropnment.

Please contact the New Relic representative to get assistance with alert policies for metrics collected from Openstack.



## Visualization

Go to the root directory of this repo and follow the instructions in the README file to locally install the High Density Nerdlet in your account. Optionally you could publish and deploy yhr nerdlet account-wide, so that it could be used by other members in the account.

Please contact the New Relic representative to import additional dashboards to your account for visualization.


