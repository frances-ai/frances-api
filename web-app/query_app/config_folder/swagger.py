template = {
    "swagger": "2.0",
    "info": {
        "title": "frances",
        "description": "API for frances",
        "version": "1.0"
    },
    "basePath": "/api/v1",
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    }
}

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger-ui": True,
    "specs_route": "/apidocs"
}

