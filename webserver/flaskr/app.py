import os
from flask import Flask
from flask import jsonify
from flask import render_template

def create_app(position_state, colour_state, test_config=None):
    app = Flask(__name__,
                static_folder='./static')

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

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/colour')
    def colour():
        return jsonify(colour_state.get_if_available())

    @app.route('/position')
    def position():
        return jsonify(position_state.get_if_available())

    return app
