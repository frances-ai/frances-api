# frances backend

This repository is the backend of  an improved version of [frances](https://github.com/francesNLP/frances/tree/main)

This project contains a flask backend (this repository), [react frontend](https://github.com/frances-ai/frances-frontend), [defoe](https://github.com/frances-ai/defoe_lib)

User can access frances here: [frances](http://35.228.63.82:3000)

---

## Local Development

### Requirements
* Python3.9
* Docker
* postgresql
* jena fuseki
* defoe

### Get source code repository, models and knowledge graph files

For the source code, run:

```bash
git clone https://github.com/frances-ai/frances-api
```

For the knowledge graphs, put them under folder `frances-api/knowledge_graphs` after downloading from here: 
* [EB-KG](https://zenodo.org/record/6673897)
* [ChapbooksScotland-KG](https://zenodo.org/record/6696686)
* [LadiesDebating-KG](https://zenodo.org/record/6686596)
* [GazetteersScotland-KG](https://zenodo.org/record/6686829)


For the pre-computed NLP results, embedding and models, download from here: [models](https://universityofstandrews907-my.sharepoint.com/:f:/g/personal/ly40_st-andrews_ac_uk/Eq-ex5z-9atOvjw1LuFri6wBIu8TdW7uLVK-QXgAu2GJQg?e=hHPhGq). 
Put them under the folder `frances-api/web_app/models`

### Install Python3.9

See instruction here: [python3.9 install](https://www.python.org/downloads/)

### Install dependencies
In the `frances-api` directory, run
```bash
pip install -r webb_app/requirements.txt
```

### Run defoe grpc server

see instructions here: [defoe](https://github.com/frances-ai/defoe_lib/blob/main/docs/setup-local.md)

### Install Docker, run postgresql and fuseki using docker

see instructions here: [docker](https://docs.docker.com/engine/install/)
 
start postgresql database and fuseki server using docker compose. In the `frances-api` directory, run
```bash
docker compose -f docker-compose.dev.yml up
```

### Upload knowledge graphs and start the backend
In the `frances-api` directory, run
```bash
sh start.sh
```


---

## Running defoe in [Dataproc](https://cloud.google.com/dataproc/docs) cluster

In addition to running defoe locally using defoe grpc server, you can also connect to your dataproc clusters to run defoe queries in frances.

### Set up defoe dataproc cluster
 We have designed dataproc initialization action scripts to automatically setup defoe running environment.
You can find these scripts in the directory: `frances-api/web_app/google_cloud/cloud_storage_init_files/init`.

Before creating the cluster, several files are required to upload to google cloud storage bucket.
#### Upload files to google cloud storage
1. [Creat a bucket](https://cloud.google.com/storage/docs/creating-buckets)
2. Create defoe.zip file from [defoe](https://github.com/frances-ai/defoe_lib). In the `defoe_lib` directory, run:
    ```bash
    zip -r defoe.zip defoe
    ```
3. Update the init scripts (line 36) :
    ```bash
   gcloud storage cp gs://<your bucket name>/defoe.zip /home/defoe.zip
   ```
4. [Upload files to the bucket](https://cloud.google.com/storage/docs/uploading-objects#upload-object-console). The required files are:
   * updated cluster init folder: `frances-api/web_app/google_cloud/cloud_storage_init_files/init`.
   * defoe.zip in step 2
   * run_query.py in [defoe](https://github.com/frances-ai/defoe_lib): `defoe_lib/run_query.py`
   * precomputedResult folder: `frances-api/web_app/query_app/precomputedResult`.
   
#### Creat the dataproc cluster using init scripts
see instructions here: [dataproc initialization actions](https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/init-actions)

#### Public fuseki server
Since defoe requires fuseki server to query knowledge graphs, we need to make it accessible to the cloud cluster.
You can follow the instruction on local development part for [fuseki install](#install-docker-run-postgresql-and-fuseki-using-docker). But here, you apply it in a cloud VM. 
Note that, you should make the fuseki accessible to the cluster by opening the port in firewall rule settings.


### Run frances locally with defoe dataproc cluster

We have built a dataproc_defoe_service to adopt the defoe dataproc cluster.
All you need to do is change the `MODE` in `frances-api/web_app/query_app/resolver.py`:

```python
# In line 25 of resolver.py
kg_base_url = "your fuseki server url"

# In line 30 of resolver.py
MODE = "gs"

# From line 68 - 76 of resolver.py
MAIN_PYTHON_FILE_URI = "gs://<your bucket name>/run_query.py"
PYTHON_FILE_URIS = ["file:///home/defoe.zip"]
PROJECT_ID = "<your project id>"
BUCKET_NAME = "<your bucket name>"
DEFAULT_CLUSTER = {
    "cluster_name": "<your cluster name>",
    "project_id": PROJECT_ID,
    "region": "<your cluster region>"
}

```
Since it uses google client library to access dataproc and cloud storage, you need to Set up Application Default Credentials in local environment
See the instructions here: https://cloud.google.com/docs/authentication/provide-credentials-adc#local-dev

After this, you can run this backend similar to above [local development process](#local-development), except you don't need to run defoe grpc server and local fuseki server. 

---

## Cloud Deployment

### Build docker image for backend:
Update the `frances-api/install_graph.sh`:
```bash
fuseki_url="http://fuseki:3030"
```

This image will also automatically upload knowledge graphs. To support multiple architectures, run the following command in `frances-api` directory to build the image:
```bash
docker buildx build --platform <linux/arm/v7,linux/arm64/v8,>linux/amd64 --tag <docker username>/frances-api:latest --push .
```
You can choose which architectures (linux/arm/v7, linux/arm64/v8, linux/amd64) to support.

### Build docker image for frontend:
[Setup frontend](https://github.com/frances-ai/frances-frontend)

Run the following command in `frances-frontend` directory to build the image:
```bash
docker buildx build --platform <linux/arm/v7,linux/arm64/v8,>linux/amd64 --tag <docker username>/frances-front:latest --push .
```

### Set up Application Default Credentials in the cloud vm

See the instructions here: https://cloud.google.com/docs/authentication/provide-credentials-adc#local-dev

If your Cloud VM has gcloud CLI installed (pre-installed in all Google Cloud VM), just run the following command:
```
gcloud auth application-default login
```

### Run all the services using docker compose

1. Update the `docker-compose.prod.yml` based on your cloud configuration.
2. Upload the `docker-compose.prod.yml` file to the cloud VM.
3. Run all services using the following command (in the same directory with uploaded docker compose file):
   ```
   sudo docker compose -f docker-compose.prod.yml up
   ```






