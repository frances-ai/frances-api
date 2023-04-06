import json
import os.path
from http import HTTPStatus
from os.path import dirname, abspath, join

from flask import Blueprint, jsonify, request, send_file

from .sparql_queries import *
from ..resolver import get_kg_type, get_files

collection = Blueprint("collection", __name__, url_prefix="/api/v1/collection")


@collection.get("/list")
def get_collections_list():
    collections_detail = get_collections_json()
    collections = list(map(lambda c: {
        "id": c["id"],
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
    image_file_path = os.path.join(get_files().images_path, "collections", image_name)
    return send_file(image_file_path, mimetype="image/jpeg")


def get_collection_by_id(collection_id):
    collections_detail = get_collections_json()
    collection_detail = next((c for c in collections_detail if c["id"] == collection_id), None)
    return collection_detail


@collection.get("/")
def get_collection_detail():
    collection_id = request.args.get("id", type=int)
    return jsonify(get_collection_by_id(collection_id)), HTTPStatus.OK


@collection.route("/eb_edition/list", methods=['GET'])
def eb_edition_list():
    return jsonify(get_editions()), HTTPStatus.OK


@collection.route("/nls_serie/list", methods=['GET'])
def nls_serie_list():
    collection_name = request.args.get("collection")
    kg_type = get_kg_type(collection_name)
    return jsonify(get_series(kg_type)), HTTPStatus.OK


@collection.route("/eb_edition", methods=['GET'])
def eb_edition():
    edition_uri = request.args.get("uri")
    edition_uri = "<" + edition_uri + ">"
    return jsonify(get_edition_details(edition_uri)), HTTPStatus.OK


@collection.route("/nls_serie", methods=['GET'])
def nls_serie():
    collection_name = request.args.get("collection")
    kg_type = get_kg_type(collection_name)
    serie_uri = request.args.get("uri")
    serie_uri = "<" + serie_uri + ">"
    return jsonify(get_serie_details(kg_type, serie_uri)), HTTPStatus.OK


@collection.get("volume/list")
def volume_list():
    collection_name = request.args.get("collection")
    kg_type = get_kg_type(collection_name)
    edition_uri = request.args.get("uri")
    edition_uri = "<" + edition_uri + ">"
    return jsonify(get_volumes(kg_type, edition_uri)), HTTPStatus.OK


@collection.get("/volume")
def volume():
    collection_name = request.args.get("collection")
    kg_type = get_kg_type(collection_name)
    volume_uri = request.args.get("uri")
    volume_uri = "<" + volume_uri + ">"
    if kg_type == "total_eb":
        return jsonify({
            "detail": get_volume_details(kg_type, volume_uri),
            "statistics": get_eb_vol_statistics(volume_uri)
        }), HTTPStatus.OK

    return jsonify({
        "detail": get_volume_details(kg_type, volume_uri)
    }), HTTPStatus.OK
