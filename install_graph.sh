#!/bin/bash

fuseki_url="http://127.0.0.1:3030"
admin_user="admin"
admin_password="pass123"
datasets=(
  "total_eb" "chapbooks_scotland" "ladies" "gazetteers_scotland"
)

# Iterate over the datasets array
for index in "${!datasets[@]}"; do
  dataset_name="${datasets[$index]}"
  file_path="knowledge_graphs/${dataset_name}.ttl"

  # Check if the dataset already exists
  dataset_exists_response=$(curl -s -o /dev/null -w "%{http_code}" -X GET -u "$admin_user:$admin_password" "$fuseki_url/$dataset_name")

  if [ "$dataset_exists_response" == "200" ]; then
    echo "Dataset ${dataset_name} already exists: $dataset_name"
  else
    # Create the dataset using the Fuseki administrative endpoint
    echo "Dataset ${dataset_name} not found, uploading to fuseki"
    create_dataset_response=$(curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "dbName=${dataset_name}&dbType=mem" -u "$admin_user:$admin_password" "$fuseki_url/\$/datasets")
    echo $create_dataset_response
    echo "Dataset created successfully: $dataset_name"

    # Load data into the dataset using the Fuseki data upload endpoint
    load_data_response=$(curl -X POST -H "Content-Type: application/x-turtle" -u "$admin_user:$admin_password" --data-binary "@$file_path" "$fuseki_url/$dataset_name/data")
    echo $load_data_response
    echo "Data loaded successfully into dataset: $dataset_name"
  fi

done