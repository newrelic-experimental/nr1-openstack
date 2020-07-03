#!/bin/bash

basedir="$(dirname $0)"
NR_AGENT_DIR="${basedir%/scripts}"

function usage() {
  echo -e "\n\tusage: $0   [ block_storage | hypervisors | servers | networks | limits | resource_providers | keystone | nova | images ]"
  echo -e "\tprocesses Openstack telemetry and pushes metrics to New Relic Insights\n\n\n"
  exit 1
}


[ -z "${1}" ] && {
  usage
}

SVC_TYPE="${1}"
CFG_FILE="${NR_AGENT_DIR}/config/os-config.json"
OUT_FILE="${NR_AGENT_DIR}/logs/os-mon-out.log"
ERR_FILE="${NR_AGENT_DIR}/logs/os-mon-err.log"

if [[ ":hypervisors:-:servers:-:networks:-:limits:-:block_storage:-:resource_providers:-:images:-:keystone:-:nova:" != *":${SVC_TYPE}:"* ]]; then
  usage
fi

mkdir -p ${NR_AGENT_DIR}/logs 2>/dev/null
python ${NR_AGENT_DIR}/os-mon.py -c ${CFG_FILE} -s ${SVC_TYPE} >> ${OUT_FILE} 2>${ERR_FILE}

DATA_FOUND=0
for file in ${NR_AGENT_DIR}/data/${SVC_TYPE}/${SVC_TYPE}_*.json
do
  if [ -s "${file}" ]; then
    DATA_FOUND=1
    break
  fi
done

if [ $DATA_FOUND != 1 ]; then
    # "no data available for ${SVC_TYPE} in this cycle"
    exit 0
fi

### cat ${NR_AGENT_DIR}/data/${SVC_TYPE}/${SVC_TYPE}_*.json | jq -s "."
echo "[ $(cat ${NR_AGENT_DIR}/data/${SVC_TYPE}/${SVC_TYPE}_*.json | grep "^{" | sed 's/}$/},/' | tr -d '\n' | sed 's/,$//') ]"
[ $? == 0 ] && {
  mkdir -p ${NR_AGENT_DIR}/data/backup/${SVC_TYPE} > /dev/null 2>/dev/null
  mv -f ${NR_AGENT_DIR}/data/${SVC_TYPE}/${SVC_TYPE}*.json ${NR_AGENT_DIR}/data/backup/${SVC_TYPE}/
  ### rm -f ${NR_AGENT_DIR}/data/${SVC_TYPE}/${SVC_TYPE}*.json
}
