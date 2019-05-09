#!python
# -*- coding: utf-8 -*-
"""WSGI Entrypoint.
"""
from tunnel_rpc.server import create_app

APP = create_app()
