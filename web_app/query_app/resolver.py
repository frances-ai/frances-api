import logging
import os

from flask import jsonify
from werkzeug.security import generate_password_hash

from .db import Database, User

from ..defoe_service.dataproc_defoe_service import DataprocDefoeService
from ..defoe_service.local_defoe_service import LocalDefoeService
from ..google_cloud.google_cloud_storage import GoogleCloudStorage

HTTP_PROTOCOL = "http://"

FRANCES_FRONT_DOMAIN_VAR_NAME = "FRANCES_FRONT_DOMAIN"
FRANCES_FRONT_PORT_VAR_NAME = "FRANCES_FRONT_PORT"
FRANCES_FRONT_DEFAULT_PORT = "3000"
FRANCES_FRONT_DEFAULT_DOMAIN = "127.0.0.1"

LOCAL_DEFOE_GRPC_CHANNEL = "localhost:5052"
LOCAL_DATABASE_HOST = "127.0.1"
DATABASE_USER = "frances"
DATABASE_PASSWORD = "frances"

database = None
defoe_service = None
cloud_storage_service = None

kg_base_url = "http://www.frances-ai.com:3030/"

if os.getenv("KG_BASE_URL"):
    kg_base_url = os.getenv("KG_BASE_URL")

MODE = "local"


def get_front_env():
    domain_var = os.getenv(FRANCES_FRONT_DOMAIN_VAR_NAME)
    if domain_var != None:
        domain = domain_var
    else:
        domain = FRANCES_FRONT_DEFAULT_DOMAIN

    port_var = os.getenv(FRANCES_FRONT_PORT_VAR_NAME)

    if port_var != None:
        port = port_var
    else:
        port = FRANCES_FRONT_DEFAULT_PORT

    if port == "80":
        address = HTTP_PROTOCOL + domain
    else:
        address = HTTP_PROTOCOL + domain + ':' + port
    return {
        'DOMAIN': domain,
        'ADDRESS': address
    }


def get_database():
    global database
    if database != None:
        return database
    database_config = {
        "host": LOCAL_DATABASE_HOST,
        "user": DATABASE_USER,
        "password": DATABASE_PASSWORD
    }
    if MODE == "deploy":
        database_config["host"] = "database"
    database = Database(database_config)
    add_init_user(database)
    return database


def add_init_user(database):
    email = "admin@frances-ai.com"
    if database.get_user_by_email(email) is not None:
        # user has been registered.
        return

    # add init user to database
    # encode password
    password = "admin123"
    first_name = "Admin"
    last_name = "Admin"
    pwd_hash = generate_password_hash(password)

    try:
        user = User.create_new(first_name=first_name, last_name=last_name, password=pwd_hash, email=email)
        database.add_active_user(user)
        logging.info("user created!")
    except Exception as e:
        print(e)
        database.rollback()




MAIN_PYTHON_FILE_URI = "gs://frances2023/run_query.py"
PYTHON_FILE_URIS = ["file:///home/defoe.zip"]
PROJECT_ID = "frances-365422"
BUCKET_NAME = "frances2023"
DEFAULT_CLUSTER = {
    "cluster_name": "cluster-8753",
    "project_id": PROJECT_ID,
    "region": "us-central1"
}


def get_file_storage_mode():
    file_model = MODE
    if MODE == "deploy":
        file_model = "gs"

    return file_model


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
    if MODE == "gs" or MODE == "deploy":
        defoe_service = DataprocDefoeService(MAIN_PYTHON_FILE_URI, PYTHON_FILE_URIS, get_cluster())
    elif MODE == "local":
        defoe_service = LocalDefoeService(channel=LOCAL_DEFOE_GRPC_CHANNEL)
    return defoe_service


def get_google_cloud_storage():
    global cloud_storage_service
    if cloud_storage_service is not None:
        return cloud_storage_service
    if get_file_storage_mode() == "gs":
        cloud_storage_service = GoogleCloudStorage(project_id=PROJECT_ID, bucket_name=BUCKET_NAME)
    return cloud_storage_service
