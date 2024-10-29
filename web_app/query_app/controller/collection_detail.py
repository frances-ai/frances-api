import json
import os.path
from http import HTTPStatus
from io import BytesIO
from os.path import dirname, abspath, join

import yaml
from flask import Blueprint, jsonify, request, send_file

from .sparql_queries import *
from ..flask_config import DefaultFlaskConfig

collection = Blueprint("collection", __name__, url_prefix="/api/v1/collection")
image_path = DefaultFlaskConfig.IMAGES_FOLDER


@collection.get("/list")
def get_collections_list():
    collections_detail = get_collections_json()
    collections = list(map(lambda c: {
        "uri": c["uri"],
        "name": c["name"],
        "image_name": c["cover_image_name_small"],
        "year_range": c["year_range"]
    }, collections_detail))
    return jsonify({
        "collections": collections
    }), HTTPStatus.OK


def get_collections_json():
    current_dir = dirname(abspath(__file__))
    collections_json_file = open(join(current_dir, "collections.json"))
    return json.load(collections_json_file)


@collection.get("/image")
def get_collection_image():
    image_name = request.args.get("name")
    image_file_path = os.path.join(image_path, "collections", image_name)
    return send_file(image_file_path, mimetype="image/jpeg")


def get_collection_by_uri(collection_uri):
    collections_detail = get_collections_json()
    collection_detail = next((c for c in collections_detail if c["uri"] == collection_uri), None)
    return collection_detail


@collection.post("/")
def get_collection_detail():
    collection_uri = request.json.get("uri")
    return jsonify(get_collection_by_uri(collection_uri)), HTTPStatus.OK


@collection.route("/eb_edition/list", methods=['GET'])
def eb_edition_list():
    return jsonify(get_editions()), HTTPStatus.OK


@collection.route("/nls_series/list", methods=['GET'])
def nls_serie_list():
    collection_name = request.args.get("collection")
    return jsonify(get_series(collection_name)), HTTPStatus.OK


@collection.route("/eb_edition", methods=['GET'])
def eb_edition():
    edition_uri = request.args.get("uri")
    edition_uri = "<" + edition_uri + ">"
    return jsonify(get_edition_details(edition_uri)), HTTPStatus.OK


@collection.route("/nls_series", methods=['GET'])
def nls_series():
    series_uri = request.args.get("uri")
    series_uri = "<" + series_uri + ">"
    return jsonify(get_series_details(series_uri)), HTTPStatus.OK


@collection.get("volume/list")
def volume_list():
    edition_series_uri = request.args.get("uri")
    edition_series_uri = "<" + edition_series_uri + ">"
    return jsonify(get_volumes(edition_series_uri)), HTTPStatus.OK


@collection.get("/volume")
def volume():
    collection_name = request.args.get("collection")
    volume_uri = request.args.get("uri")
    if collection_name == 'Encyclopaedia Britannica':
        return jsonify({
            "detail": get_volume_details(volume_uri),
            "statistics": get_eb_vol_statistics(volume_uri)
        }), HTTPStatus.OK

    return jsonify({
        "detail": get_volume_details(volume_uri)
    }), HTTPStatus.OK


@collection.post("/es/download")
def download_es_full_details():
    es_uri = request.json.get("uri")
    # Get edition or series full details
    es_full_details, es_type = get_es_full_details(es_uri)
    # Convert the edition or series full details to YAML
    yaml_data = yaml.dump(es_full_details)

    # Create a file-like object in memory (BytesIO)
    yaml_file = BytesIO()
    yaml_file.write(yaml_data.encode('utf-8'))
    yaml_file.seek(0)  # Reset file pointer to the beginning

    # Send the file as a response
    filename = es_type + es_full_details[es_type]["MMSID"] + ".yml"
    return send_file(
        yaml_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/x-yaml'
    )


@collection.post("/volume/download")
def download_volume_full_details():
    volume_uri = request.json.get("uri")
    # Get volume full details
    volume_full_details = get_volume_full_details(volume_uri)
    # Convert the volume full details to YAML
    yaml_data = yaml.dump(volume_full_details)

    # Create a file-like object in memory (BytesIO)
    yaml_file = BytesIO()
    yaml_file.write(yaml_data.encode('utf-8'))
    yaml_file.seek(0)  # Reset file pointer to the beginning

    # Send the file as a response
    filename = "volume" + volume_full_details["volume"]["id"] + ".yml"
    return send_file(
        yaml_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/x-yaml'
    )
