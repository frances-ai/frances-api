import os
import json
import requests

from .db import Database, DatabaseConfig

from .controller.models import ModelsRepository
from .controller.files import FilesConfig
from .defoe_service import DefoeService
from ..google_cloud.google_cloud_storage import GoogleCloudStorage

CONSUL_VAR_NAME = "CONSUL_ADDRESS"
CONSUL_PROTOCOL = "http://"
CONSUL_DEFAULT_ADDRESS = "localhost:8500"
CONFIG_PATH = "/v1/kv/frances/config?raw"

FRANCES_FRONT_DOMAIN_VAR_NAME = "FRANCES_FRONT_DOMAIN"
FRANCES_FRONT_PORT_VAR_NAME = "FRANCES_FRONT_PORT"
FRANCES_FRONT_DEFAULT_PORT = "3000"
FRANCES_FRONT_DEFAULT_DOMAIN = "127.0.0.1"

config = None
frances = None
models = None
database = None
defoe_service = None
cloud_storage_service = None


class QueryAppConfig:
    def __init__(self):
        self.database = None
        self.files = None

    @staticmethod
    def from_json(text):
        vals = json.loads(text)
        config = QueryAppConfig()
        config.frances = FrancesConfig.from_dict(vals["frances"])
        config.database = DatabaseConfig.from_dict(vals["database"])
        return config


class FrancesConfig:
    def __init__(self, files=None):
        self.files = files

    @staticmethod
    def from_dict(vals):
        config = FrancesConfig()
        config.files = FilesConfig.from_dict(vals["files"])
        return config


def get_config_url():
    consul_var = os.getenv(CONSUL_VAR_NAME)
    consul_address = None

    if consul_var != None:
        consul_address = consul_var
    else:
        consul_address = CONSUL_DEFAULT_ADDRESS

    return CONSUL_PROTOCOL + consul_address + CONFIG_PATH


def get_front_env():
    domain_var = os.getenv(FRANCES_FRONT_DOMAIN_VAR_NAME)
    domain = None

    if domain_var != None:
        domain = domain_var
    else:
        domain = FRANCES_FRONT_DEFAULT_DOMAIN

    port_var = os.getenv(FRANCES_FRONT_PORT_VAR_NAME)
    port = None

    if port_var != None:
        port = port_var
    else:
        port = FRANCES_FRONT_DEFAULT_PORT
    return {
        'DOMAIN': domain,
        'ADDRESS': CONSUL_PROTOCOL + domain + ':' + port
    }


def get_config():
    global config
    if config != None:
        return config
    url = get_config_url()
    print("Resolved consul address as: " + url)

    resp = requests.get(url)
    print("Consul config retrieved:")
    print(resp.text)

    config = QueryAppConfig.from_json(resp.text)
    return config


def get_frances():
    # this is only a config
    return get_config().frances


def get_files():
    # this is only a config
    return get_frances().files


kg_types_map = {
    'Encyclopaedia Britannica': 'total_eb',
    'Chapbooks printed in Scotland': 'chapbooks_scotland',
    'Ladies’ Edinburgh Debating Society': 'ladies',
    'Gazetteers of Scotland': 'gazetteers_scotland'
}


def get_kg_type(collection):
    return kg_types_map[collection]


DEFAULT_KG_BASE_URL = "http://35.228.63.82:3030/"


def get_kg_url(kg_type):
    kg_base_url = os.getenv("KG_BASE_URL")
    if kg_base_url is None:
        kg_base_url = DEFAULT_KG_BASE_URL
    return kg_base_url + kg_type + "/sparql"


def get_models():
    global models
    if models != None:
        return models
    models = ModelsRepository(get_files())
    return models


def get_database():
    global database
    if database != None:
        return database
    database = Database(get_config().database)
    return database


MAIN_PYTHON_FILE_URI = "gs://frances2023/run_query.py"
PYTHON_FILE_URIS = ["file:///home/defoe.zip"]
PROJECT_ID = "frances-365422"
BUCKET_NAME = "frances2023"
DEFAULT_CLUSTER = {
    "cluster_name": "cluster-8753",
    "project_id": PROJECT_ID,
    "region": "us-central1"
}


def get_cluster():
    cluster_name = os.getenv("CLUSTER_NAME")
    cluster_region = os.getenv("CLUSTER_REGION")
    if cluster_name:
        return {
            "cluster_name": cluster_name,
            "project_id": PROJECT_ID,
            "region": cluster_region
        }
    return DEFAULT_CLUSTER


def get_defoe_service():
    global defoe_service
    if defoe_service is not None:
        return defoe_service
    defoe_service = DefoeService(MAIN_PYTHON_FILE_URI, PYTHON_FILE_URIS, get_cluster())
    return defoe_service


def get_google_cloud_storage():
    global cloud_storage_service
    if cloud_storage_service is not None:
        return cloud_storage_service
    cloud_storage_service = GoogleCloudStorage(project_id=PROJECT_ID, bucket_name=BUCKET_NAME)
    return cloud_storage_service
