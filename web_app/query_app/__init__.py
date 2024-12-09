#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Make the Flask app available."""
import logging

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config_folder.swagger import swagger_config, template
from .controller.auth import auth, auth_protected
from .controller.query import query, query_protected
from .controller.search import search
from .controller.collection_detail import collection
from .controller.stats import stats
from .core import limiter

from .flask_config import DefaultFlaskConfig


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    limiter.init_app(app)
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    if test_config is None:
        app.config.from_object(DefaultFlaskConfig())
    else:
        app.config.from_mapping(test_config)

    # Set up openapi
    Swagger(app, config=swagger_config, template=template)

    # Use JWT authentication
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(stats)
    app.register_blueprint(auth)
    app.register_blueprint(auth_protected)
    app.register_blueprint(query)
    app.register_blueprint(query_protected)
    app.register_blueprint(collection)
    app.register_blueprint(search)
    # Enable CORS
    CORS(app)
    return app
