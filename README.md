# Deployment
## Local

Run this when you want to use frances on your own machine.

### Clone repositories
Each repository should be cloned into the `/deploy` directory, as shown below:
```
 deploy/
 ├── frances-api/
 └── defoe_lib/
```

In other words, both repos are cloned into this directory.

### Build frances-api docker image

Run the following from the `/deploy` directory:

`docker build --tag frances-api --label frances-api .`

### Start the required local services

Run the following from the `/deploy` directory:

`docker compose -f docker-compose.local.yml up`

Verify that each service has been started successfully.

### Upload the knowledge graph to Apache Fuseki

Create a dataset with the name `total_eb`, uploading the file `total_eb.ttl` to it.

### Edit the config entry in Consul

Open the Consul web UI on `localhost:8500` and look at the key called `frances/config`. By default, this will have the values given in the file `./data/config.json`. You shouldn't need to edit this at all when functioning properly.

## Development

Run this when you want to develop/change the code of `frances-api` and `defoe_lib`.

### Clone repositories
Each repository should be cloned into the same folder, as shown below:
```
 .
 ├── deploy/
 ├── frances-api/
 └── defoe_lib/
```

### Start the required local services

Run the following from the `/deploy` directory:

`docker compose -f docker-compose.dev.yml up`

Verify that each service has been started successfully.

### Upload the knowledge graph to Apache Fuseki

Create a dataset with the name `total_eb`, uploading the file `total_eb.ttl` to it.

### Create a config entry in Consul

Open the Consul web UI on `localhost:8500` and create a key called `frances/config` with the values given in the file `deploy/dev-config.json`.

### Start the backend server

Run the following from the root directory:

`python -m frances-api.web_app`

