import logging

from flasgger import swag_from
from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
import sendgrid
from sendgrid.helpers.mail import Mail
from ..flask_config import DefaultFlaskConfig

from ..db import User

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
auth_protected = Blueprint("auth_protected", __name__, url_prefix="/api/v1/protected/auth")
database = DefaultFlaskConfig.DATABASE


def validate_register_info(first_name, last_name, email, password):
    if len(password) < 6:
        raise Exception('Password is too short')

    if len(first_name) == 0 or len(last_name) == 0 or len(password) == 0 or len(email) == 0:
        raise Exception('Required register info can not be empty')

    if not validators.email(email):
        raise Exception('Email is not valid')

    if database.get_user_by_email(email) is not None:
        raise Exception('Email has been registered')


@auth.post("/emailRegistered")
@swag_from("../docs/auth/emailRegistered.yml")
def email_registered():
    email = request.json['email']
    if not validators.email(email):
        return jsonify({
            "error": 'Email is not valid'
        }), HTTPStatus.BAD_REQUEST

    registered = False
    if database.get_user_by_email(email) is not None:
        registered = True

    return jsonify({
        "registered": registered
    }), HTTPStatus.OK


def send_approval_email(user_details):
    admin_email = current_app.config["ADMIN_EMAIL"]
    message = Mail(
        from_email=admin_email,
        to_emails=admin_email,
        subject='New User Account Approval',
        plain_text_content=f"Please approve the account for {user_details.first_name}  {user_details.last_name}({user_details.email})."
    )
    sg = sendgrid.SendGridAPIClient(api_key=current_app.config["SENDGRID_API_KEY"])
    response = sg.send(message)
    print(response.status_code)


@auth.post("/register")
@swag_from("../docs/auth/register.yml")
def register():
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    password = request.json['password']

    try:
        validate_register_info(first_name, last_name, email, password)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), HTTPStatus.BAD_REQUEST

    # encode password
    pwd_hash = generate_password_hash(password)

    try:
        # Create user account and store it to database
        user = User.create_new(first_name=first_name, last_name=last_name, password=pwd_hash, email=email)
        database.add_user(user)
        # Send admin the register information for approval.
        send_approval_email(user)
        return jsonify({
            "user": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            }
        }), HTTPStatus.OK
    except Exception as e:
        database.rollback()
        return jsonify({
            "error": str(e)
        }), HTTPStatus.BAD_REQUEST


@auth.post("/login")
@swag_from("../docs/auth/login.yml")
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    # Validate email and password
    if len(email) == 0 or len(password) == 0:
        return jsonify({
            "error": 'Required login info can not be empty'
        }), HTTPStatus.BAD_REQUEST

    user = database.get_active_user_by_email(email)

    if user:
        pwd_correct = check_password_hash(user.password, password)

        if pwd_correct:
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            response = jsonify({
                "user": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email
                }
            })

            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)

            return response, HTTPStatus.OK

    return jsonify({
        "error": "wrong credential"
    }), HTTPStatus.UNAUTHORIZED


@auth.post('/logout')
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


@auth_protected.get("/profile")
@jwt_required()
@swag_from("../docs/auth/profile.yml")
def profile():
    user_id = get_jwt_identity()
    user = database.get_active_user_by_id(user_id)
    if user:
        return jsonify({
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }
        }), HTTPStatus.OK
    else:
        return jsonify({
            "error": "user does not exist"
        }), HTTPStatus.UNAUTHORIZED
