import os
from flask import Flask, jsonify


def create_app(position_state, colour_state, test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/colour')
    def colour():
        return jsonify(colour_state.get_if_available())

    @app.route('/position')
    def position():
        return jsonify(position_state.get_if_available())

    return app
