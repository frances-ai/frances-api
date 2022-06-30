import os
from pathlib import Path

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

UPLOAD_FOLDER="/Users/damonyu/Documents/CS5098/frances-api/web-app/query_app/upload_folder"

CONFIG_FOLDER="/Users/damonyu/Documents/CS5098/frances-api/web-app/query_app/config_folder"

RESULTS_FOLDER="/Users/damonyu/Documents/CS5098/frances-api/web-app/query_app/defoe_results"

ALLOWED_EXTENSIONS = {'txt', 'yaml', 'yml'}
