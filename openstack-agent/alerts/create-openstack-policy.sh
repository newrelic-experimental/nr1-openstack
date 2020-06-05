#!/bin/bash

trap 'err_report $LINENO' ERR
trap 'cleanup' 3 9 15

function usage() {
  echo -e "\n\tusage: $0   [Command options]\n"
  echo -e "\t\tCommand options:"
  echo -e "\t\t\t-v: verbose"
  echo -e "\t\t\t-d: debug"
  echo -e "\t\t\t-k: admin api key for target rpm account"
  echo -e "\t\t\t-p: policy name (default: OpenStack)\n\n"
  echo "exit ${1}"
  exit ${1}
}

function cleanup() {
  echo -e "\ncleaning up...\n"
  if [ "${1}" -le "1" ]
  then
    echo "removing temporary files"
    rm -f ${temp_outfile} 
    rm -f ${temp_errfile}
  else
    exit ${1}
  fi
}

function err_report() {
  echo "${0}: Error on line ${1:-"Unknown Error"}" 1>&2
  cleanup $1
}

function checkStatus() {
  exitcode=${1}
  outfile=${2}
  errfile=${3}
  http_status_code=$(cat ${outfile} | tail -c 3)
  echo "http_status_code: ${http_status_code}"
  if [ ${http_status_code} -lt 200 -o ${http_status_code} -gt 299 ]
  then
    echo "http status code: ${http_status_code}"
    [ -s "${outfile}" ] && {
      echo -e "out >> $(cat ${outfile})\n"
    }
    [ -s "${errfile}" ] && {
      echo -e "err >> $(cat ${errfile})\n"
    }
    cleanup ${exitcode}
  fi
}

### check if ploicy with this name exists
function checkPolicyName() {
  policyExists=$(curl -sk -X GET 'https://api.newrelic.com/v2/alerts_policies.json' \
      -H "X-Api-Key: ${targetAdminKey}" -H "Content-Type: application/json" \
      -G -d "filter[name]=${policyName}&filter[exact_match]=true" | \
      jq ".policies | length")

  if [ ${policyExists} -gt 0 ]
  then
    echo -e "\n\tPolicy name ${policyName} exists..."
    policyName="${policyName}-nr-os-$((${policyExists}+1))-$(date '+%s')"
    echo -e "\tCreating New Policy as ${policyName}"
    echo -e "\tYou could change the name in New Relic Alerts UI as you wish\n\n"
  fi
}

### create alert policy:
function createPolicy() {
  policy="{\"policy\": {\"name\": \"$policyName\", \"incident_preference\": \"PER_CONDITION_AND_TARGET\"}}"
  [ $debug ] && {
    echo "${policy}"
  }
  policyId=$(curl -sk -X POST "https://api.newrelic.com/v2/alerts_policies.json" \
       -H "X-Api-Key: ${targetAdminKey}" -H "Content-Type: application/json" \
       -d "${policy}" | tee ${temp_outfile} | jq ".policy.id")
}

### create alert conditions
function createAlertConditions() {
  echo -e "\n>> creating alert conditions..."
  cat openstack_alert_conditions.json | while read alert_condition
  do
    curl -sk -w '%{http_code}' -X POST "https://api.newrelic.com/v2/alerts_conditions/policies/${policyId}.json" \
        -H "X-Api-Key: ${targetAdminKey}" -H "Content-Type: application/json" \
        -d "${alert_condition}" > ${temp_outfile} 2>${temp_errfile}
    [ $debug ] && {
      echo -e "out >> $(cat ${temp_outfile})\n"
    }
    checkStatus 3 ${temp_outfile} ${temp_errfile}
  done
}

### create nrql alert conditions
function createNrqlAlertConditions() {
  echo -e "\n>> creating nrql alert conditions..."
  cat openstack_nrql_alert_conditions.json | while read nrql_alert_condition
  do
    curl -sk -w '%{http_code}' -X POST "https://api.newrelic.com/v2/alerts_nrql_conditions/policies/${policyId}.json" \
        -H "X-Api-Key: ${targetAdminKey}" -H "Content-Type: application/json" \
        -d "${nrql_alert_condition}" > ${temp_outfile} 2>${temp_errfile}
    [ $debug ] && {
      echo -e "out >> $(cat ${temp_outfile})\n"
    }
    checkStatus 4 ${temp_outfile} ${temp_errfile}
  done
}

### create infra alert conditions
function createInfraAlertConditions() {
  echo -e "\n>> creating infra alert conditions..."
  cat openstack_infrastructure_alert_conditions.json | while read condition
  do
    infra_alert_condition=$(echo ${condition} | sed "s/\(\"policy_id\" *: *\)[[:digit:]]*\(,\)/\1${policyId}\2/")
    curl -sk -w '%{http_code}' -X POST "https://infra-api.newrelic.com/v2/alerts/conditions" \
        -H "X-Api-Key: ${targetAdminKey}" -H "Content-Type: application/json" \
        -d "${infra_alert_condition}" > ${temp_outfile} 2>${temp_errfile}
    [ $debug ] && {
      echo -e "out >> $(cat ${temp_outfile})\n"
    }
    checkStatus 5 ${temp_outfile} ${temp_errfile}
  done
}

### __main__ ================================================
unset verbose debug

temp_outfile="openstack_alerts_$$.out"
temp_errfile="openstack_alerts_$$.err"
targetAdminKey=""
policyName="OpenStack"
policyId=""

# echo "cmd args: ${@}"
# echo "args count: ${#}"
while getopts "h?vdk:p:" opt; do
    # echo "option index: ${OPTIND}"
    case "$opt" in
    h|\?)
        usage
        exit 1
        ;;
    v)  verbose=true
        ;;
    d)  debug=true
        ;;
    k)  targetAdminKey=$OPTARG
        ;;
    p)  policyName=$OPTARG
        ;;
    esac
done


if [ $verbose ]; then
	set -x
fi

if [ $debug ]; then
  echo "cmd args: ${@}"
  echo "args count: ${#}"
fi

[ -z "${targetAdminKey}" ] && {
	echo -e "\n\n\tError: Target Account's Admin API Key not specified"
	echo -e "\tPlease use command line option \"-k\" to specify the target account's admin API key\n"
	usage
}
echo -e "\n\ttarget admin Key: ${targetAdminKey} -- policy name: ${policyName}\n\n"



###
checkPolicyName
echo -e "\n>> policy name: ${policyName}"
createPolicy
echo -e "\n>> policy created -- policy id: ${policyId}\n\n"
createAlertConditions
echo -e "\n>> alert conditions created"
createNrqlAlertConditions
echo -e "\n>> nrql alert conditions created"
createInfraAlertConditions
echo -e "\n>> infrastructure alert conditions created"
######

cleanup 0
echo -e "\nAll Done.\n"

