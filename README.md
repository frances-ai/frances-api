# Deploying this project locally
## Clone repositories
Each repository should be cloned into the same folder, as shown below:
```
 .
 ├── deploy/
 ├── frances-api/
 └── defoe_lib/
```

## Start the required local services

Run the following from the `/deploy` directory:

`docker compose up`

Verify that each service has been started successfully.

## Upload the knowledge graph to Apache Fuseki

Create a dataset with the name `total_eb`, uploading the file `total_eb.ttl` to it.

## Create a config entry in Consul

Open the Consul web UI on `localhost:8500` and create a key called `frances/config` with the values given in the file `deploy/local-config.json`.

## Start the backend server

Run the following from the root directory:

`python -m frances-api.web_app`

