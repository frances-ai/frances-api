#!/bin/sh

# Address within a docker network
consul_addr="consul"

config_file="./data/config.json"
consul_url="http://${consul_addr}:8500/v1/kv/frances/config"

# Check consul for the uploaded config
consul_response=$(
  curl -X GET $consul_url \
  --write-out %{http_code} \
  --silent \
  --output /dev/null
  )

# If needed, set consul key/value
if [[ "$consul_response" == 404 ]] ; then
  consul_config=`cat ${config_file}`
  curl -X PUT -d "$consul_config" $consul_url
fi

