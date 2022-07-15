#!/bin/sh
# Warning: this script a work in progress.

# Set Consul key/value
config=`cat local-config.json`
curl -X PUT -d "$config" http://127.0.0.1:8500/v1/kv/frances/config

# Start backend server
cd ..
python -m frances-api.web_app
