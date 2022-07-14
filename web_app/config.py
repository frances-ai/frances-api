import os
from pathlib import Path
from datetime import timedelta

from rdflib.namespace import Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import SKOS, DOAP, FOAF, DC, DCTERMS

DEBUG = True

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
SECRET_KEY = os.urandom(64)

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

UPLOAD_FOLDER = BASE_DIR + "/query_app/upload_folder"

CONFIG_FOLDER = "BASE_DIR + /query_app/config_folder"

RESULTS_FOLDER = BASE_DIR + "/query_app/defoe_results"

ALLOWED_EXTENSIONS = {'txt', 'yaml', 'yml'}

# Database
SQLALCHEMY_DATABASE_URI = 'postgresql://frances:frances@localhost:5432/frances'
SQLALCHEMY_TRACK_MODIFICATIONS = False

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

# Set the cookie paths, so that you are only sending your access token
# cookie to the access endpoints, and only sending your refresh token
# to the refresh endpoint.
JWT_ACCESS_COOKIE_PATH = '/api/'
JWT_REFRESH_COOKIE_PATH = '/api/v1/auth/token/refresh'

# Enable csrf double submit protection. See this for a thorough
# explanation: http://www.redotheweb.com/2015/11/09/api-security.html
JWT_COOKIE_CSRF_PROTECT = False

# JWT Authentication
JWT_SECRET_KEY = 'JWT_SECRET_KEY'

# Make access token lives short while refresh token lives long
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
