#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Injest Data and Run the SPARQL Query webapp."""

from query_app import create_app


if __name__ == '__main__':
    app = create_app()
    app.run()
