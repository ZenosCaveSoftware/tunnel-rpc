# -*- coding: utf-8 -*-
"""Main server factory for flask cli.

"""
from __future__ import print_function
from flask import Flask, request, Response
from jsonrpcserver import dispatch, method
from tunnel_rpc.methods import run

__all__ = ["create_app"]


def create_app():
    """Create Flask endpoint.

    Accepts and executes command requests from JSON data.

    Returns:
        (Flask) Application for execution.

    """
    app = Flask(__name__)

    method(run)

    @app.route("/", methods=["POST"])
    def index():  # pragma pylint: disable=unused-variable
        """Index to run RPC POST requests.

        Returns:
            (Response) HTTP response to RPC call.

        """
        req = request.get_data().decode()
        response = dispatch(req, debug=True)
        return Response(
            str(response), 200, mimetype="application/json"
        )

    return app
