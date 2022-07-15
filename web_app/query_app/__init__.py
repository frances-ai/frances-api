#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Make the Flask app available."""
from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager

from .config_folder.swagger import swagger_config, template
from .controller.auth import auth
from .controller.query import query

from .flask_config import DefaultFlaskConfig

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        app.config.from_object(DefaultFlaskConfig())
    else:
        app.config.from_mapping(test_config)

    # Set up openapi
    Swagger(app, config=swagger_config, template=template)

    # Use JWT authentication
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(query)
    return app
