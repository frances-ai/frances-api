from http import HTTPStatus

from flask import Blueprint, request, jsonify

from ..db import Visit
from ..resolver import database

stats = Blueprint("stats", __name__, url_prefix="/api/v1/stats")


@stats.post("/add_visit")
def add_visit():
    ip_address = request.remote_addr
    page = request.json.get("page", '/')
    try:
        visit = Visit.create_new(ip_address, page)
        database.add_visit(visit)
        return jsonify({
            "visit": {
                "ip": ip_address,
                "page": page
            }
        }), HTTPStatus.OK
    except Exception as e:
        database.rollback()
        return jsonify({
            "error": str(e)
        }), HTTPStatus.BAD_REQUEST


@stats.get("/num_visit")
def get_number_of_visits():
    try:
        number_of_visits = database.get_number_of_visits()
        return jsonify(number_of_visits), HTTPStatus.OK
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), HTTPStatus.BAD_REQUEST


