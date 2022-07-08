from flasgger import swag_from
from flask import Blueprint, request, jsonify
from http import HTTPStatus
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash

from ..db import User, db

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def validate_register_info(name, email, password):
    if len(password) < 6:
        raise Exception('Password is too short')

    if len(name) == 0 or len(password) == 0 or len(email) == 0:
        raise Exception('Required register info can not be empty')

    if not validators.email(email):
        raise Exception('Email is not valid')

    if db.get_user_by_email(email) is not None:
        raise Exception('Email has been registered')


@auth.post("/register")
@swag_from("../docs/auth/register.yml")
def register():
    name = request.json['name']
    email = request.json['email']
    password = request.json['password']

    try:
        validate_register_info(name, email, password)
    except Exception as e:
        return jsonify({
            "error": str(e)
        })

    # encode password
    pwd_hash = generate_password_hash(password)

    user = User.create_new(name=name, password=pwd_hash, email=email)
    db.add_user(user)

    return jsonify({
        "message": "User created",
        "User": {
            "name": name,
            "email": email
        }
    }), HTTPStatus.OK


@auth.post("/login")
@swag_from("../docs/auth/login.yml")
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = db.get_user_by_email(email)

    if user:
        pwd_correct = check_password_hash(user.password, password)

        if pwd_correct:
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            response = jsonify({
                "user": {
                    "name": user.name,
                    "email": user.email
                }
            })

            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)

            return response, HTTPStatus.OK

    return jsonify({
        "error": "wrong credential"
    }), HTTPStatus.UNAUTHORIZED


@auth.post('logout')
@swag_from("../docs/auth/logout.yml")
def logout():
    response = jsonify({'logout': True})
    unset_jwt_cookies(response)
    return response, HTTPStatus.OK


@auth.post("/token/refresh")
@jwt_required(refresh=True)
@swag_from("../docs/auth/refresh.yml")
def refresh_token():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    response = jsonify({
        "refresh": True
    })
    set_access_cookies(response, access_token)
    return response, HTTPStatus.OK


@auth.get("/profile")
@jwt_required()
@swag_from("../docs/auth/profile.yml")
def profile():
    user_id = get_jwt_identity()
    user = db.get_user_by_id(user_id)
    return jsonify({
        "user": {
            "name:": user.name,
            "email": user.email
        }
    }), HTTPStatus.OK
