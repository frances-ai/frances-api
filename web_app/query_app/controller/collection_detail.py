import json
import os.path
from http import HTTPStatus
from os.path import dirname, abspath

from flask import Blueprint, jsonify, request, send_file

from .sparql_queries import *

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
    print(collections)
    return jsonify({
        "collections": collections
    }), HTTPStatus.OK


def get_collections_json():
    current_dir = dirname(abspath(__file__))
    collections_json_file = open(os.path.join(current_dir, "collections.json"))
    return json.load(collections_json_file)


@collection.get("/image")
def get_collection_image():
    image_name = request.args.get("name")
    image_file_path = "/Users/ly40/Documents/frances-ai/frances-api/web_app/images/collections/" + image_name
    return send_file(image_file_path, mimetype="image/jpeg")


def get_collection_by_id(collection_id):
    collections_detail = get_collections_json()
    collection_detail = next((c for c in collections_detail if c["id"] == collection_id), None)
    return collection_detail


@collection.get("/")
def get_collection_detail():
    collection_id = request.args.get("id")
    return get_collection_by_id(collection_id)


@collection.route("/eb_details", methods=['POST'])
def eb_details():
    edList = get_editions()
    if 'edition_selection' in request.json and 'volume_selection' in request.json:
        ed_raw = request.json.get('edition_selection')
        vol_raw = request.json.get('volume_selection')
        if vol_raw != "" and ed_raw != "":
            ed_uri = "<" + ed_raw + ">"
            ed_r = get_editions_details(ed_uri)
            vol_uri = "<" + vol_raw + ">"
            ed_v = get_volume_details(vol_uri)
            ed_st = get_vol_statistics(vol_uri)
            ed_name = edList[ed_raw]
            vol_name = get_vol_by_vol_uri(vol_uri)
            return jsonify({
                "editionList": edList,
                "edition": {
                    "name": ed_name,
                    "details": ed_r,
                },
                "volume": {
                    "name": vol_name,
                    "details": ed_v,
                    "statistics": ed_st,
                },
            }), HTTPStatus.OK

    return jsonify({
        "editionList": edList,
    }), HTTPStatus.OK


@collection.route("/eb_editions", methods=['POST'])
def eb_edition_list():
    return jsonify({
        "editionList": get_editions()
    }), HTTPStatus.OK


@collection.route("/vol_details", methods=['POST'])
def vol_details():
    uri_raw = request.json.get('edition_selection')
    uri = "<" + uri_raw + ">"
    volList = get_volumes(uri)
    OutputArray = []
    for key, value in sorted(volList.items(), key=lambda item: item[1]):
        outputObj = {'id': key, 'name': value}
        OutputArray.append(outputObj)
    return jsonify(OutputArray)
