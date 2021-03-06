# -*- coding: utf-8 -*-
#
# This file is part of ClaimStore.
# Copyright (C) 2015 CERN.
#
# ClaimStore is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# ClaimStore is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ClaimStore; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307,
# USA.

"""Flask app creation."""

from flask import Flask, jsonify, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy

from claimstore.core.exception import RestApiException

db = SQLAlchemy()


def handle_restful_exceptions(error):
    """Handle invalid restful request exception."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def create_app():
    """Create Flask app using the factory."""
    app = Flask(__name__)

    # Configuration
    app.config.from_object('claimstore.config')

    # Blueprints
    from claimstore.restful import blueprint as restful_bp
    from claimstore.views import blueprint as views_bp
    app.register_blueprint(restful_bp)
    app.register_blueprint(views_bp)

    # Database
    db.init_app(app)

    # Register exceptions
    app.register_error_handler(RestApiException, handle_restful_exceptions)

    @app.errorhandler(404)
    def not_found(error):
        if 'application/json' in request.headers['Content-Type']:
            return jsonify({
                'status': 'error',
                'message': 'Resource not found.'}), 404
        return render_template('404.html'), 404

    return app
