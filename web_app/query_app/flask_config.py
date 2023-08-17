import os
from pathlib import Path
from datetime import timedelta

from rdflib.namespace import Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import SKOS, DOAP, FOAF, DC, DCTERMS

from .resolver import get_front_env, get_file_storage_mode, kg_base_url, get_database, get_defoe_service, get_google_cloud_storage


class DefaultFlaskConfig:
    DEBUG = True

    BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
    SECRET_KEY = os.urandom(64)

    WEB_APP_DIR = BASE_DIR.parent.absolute()

    # Prefixes and namespaces to use.
    NAMESPACES = dict(
        rdf=RDF,
        rdfs=RDFS,
        owl=OWL,
        xsd=XSD,
        skos=SKOS,
        doap=DOAP,
        foaf=FOAF,
        dc=DC,
        dcterms=DCTERMS,
    )

    # URLs from which to download RDF data.
    RDF_URLS = []

    PARSERS = {
        ".rdf": "xml",
        ".n3": "n3",
        ".ttl": "turtle",
        ".xml": "xml",
    }

    KG_TYPES_MAP = {
        'Encyclopaedia Britannica': 'total_eb',
        'Chapbooks printed in Scotland': 'chapbooks_scotland',
        'Ladies’ Edinburgh Debating Society': 'ladies',
        'Gazetteers of Scotland': 'gazetteers_scotland'
    }

    CONFIG_FOLDER = str(BASE_DIR) + "/config_folder"

    IMAGES_FOLDER = str(WEB_APP_DIR) + "/images"

    MODELS_FOLDER = str(WEB_APP_DIR) + "/models"

    FILE_STORAGE_MODE = get_file_storage_mode()

    if FILE_STORAGE_MODE == "gs":
        UPLOAD_FOLDER = "upload_folder"
        RESULTS_FOLDER = "defoe_results"
    else:
        UPLOAD_FOLDER = str(BASE_DIR) + "/upload_folder"
        RESULTS_FOLDER = str(BASE_DIR) + "/defoe_results"

    DATABASE = get_database()

    KG_BASE_URL = kg_base_url

    DEFOE_SERVICE = get_defoe_service()

    GOOGLE_CLOUD_STORAGE = get_google_cloud_storage()

    ALLOWED_EXTENSIONS = {'txt', 'yaml', 'yml'}

    SENDGRID_API_KEY = "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"
    ADMIN_EMAIL = "damonyu97@gmail.com"

    # OpenAPI
    SWAGGER = {
        'title': "frances API",
        'uiversion': 3
    }

    # The following JWT configuration is an example from:
    # https://flask-jwt-extended.readthedocs.io/en/3.0.0_release/tokens_in_cookies/
    # Configure application to store JWTs in cookies.
    JWT_TOKEN_LOCATION = 'cookies'

    # Only allow JWT cookies to be sent over https. In production, this should likely be True
    JWT_COOKIE_SECURE = False

    JWT_COOKIE_DOMAIN = get_front_env()['DOMAIN']

    # Set the cookie paths, so that you are only sending your access token
    # cookie to the access endpoints, and only sending your refresh token
    # to the refresh endpoint.
    JWT_ACCESS_COOKIE_PATH = '/api/v1/protected'
    JWT_REFRESH_COOKIE_PATH = '/api/v1/auth/token/refresh'

    # Enable csrf double submit protection. See this for a thorough
    # explanation: http://www.redotheweb.com/2015/11/09/api-security.html
    JWT_COOKIE_CSRF_PROTECT = True

    # JWT Authentication
    JWT_SECRET_KEY = 'JWT_SECRET_KEY'

    # Make access token lives short while refresh token lives long
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # CORS - uncomment it and change the domain in production
    CORS_ORIGINS = get_front_env()['ADDRESS']
    CORS_SUPPORTS_CREDENTIALS = True
