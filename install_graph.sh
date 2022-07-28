#!/bin/sh

# Address within a docker network
fuseki_addr="fuseki"

graph_file="/data/total_eb.ttl"

dataset="total_eb"
create_dataset_url="http://${fuseki_addr}:3030/$/datasets"
dataset_url="http://${fuseki_addr}:3030/$/datasets/${dataset}"
upload_data_url="http://${fuseki_addr}:3030/${dataset}/data"
fuseki_admin_password="pass123"

# Check fuseki for the uploaded knowledge graph
fuseki_response=$(
  curl -X GET $dataset_url \
  -H "Authorization: Basic $(echo -n admin:${fuseki_admin_password} | base64)" \
  --write-out %{http_code} \
  --silent \
  --output /dev/null
  )

# If not found, upload the file
if [[ "$fuseki_response" == 404 ]] ; then
  echo "Dataset not found, uploading to fuseki"
  curl -X POST $create_dataset_url \
    -H "Authorization: Basic $(echo -n admin:${fuseki_admin_password} | base64)" \
    -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
    --data "dbName=${dataset}&dbType=mem"
  
  upload=$(
    curl -X POST $upload_data_url \
      -H "Authorization: Basic $(echo -n admin:${fuseki_admin_password} | base64)" \
      -H "Content-Type: text/turtle;charset=utf-8" \
      --data-binary "@$graph_file"
    )
  echo $upload
fi
