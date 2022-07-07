from flasgger import swag_from
from flask import Blueprint, request, jsonify
from http import HTTPStatus
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
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

    if User.query.filter_by(email=email).first() is not None:
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

    user = User(name=name, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

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

    user = User.query.filter_by(email=email).first()

    if user:
        pwd_correct = check_password_hash(user.password, password)

        if pwd_correct:
            access = create_access_token(identity=user.id)
            refresh = create_refresh_token(identity=user.id)

            return jsonify({
                "user": {
                    "access": access,
                    "refresh": refresh,
                    "username": user.name,
                    "email": user.email
                }
            })

    return jsonify({
        "error": "wrong credential"
    })


@auth.get("/profile")
@jwt_required()
@swag_from("../docs/auth/profile.yml")
def profile():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "user": {
            "name:": user.name,
            "email": user.email
        }
    }), HTTPStatus.OK
