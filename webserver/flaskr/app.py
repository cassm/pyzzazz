import os
import sys
import inspect
from flask import Flask
from flask import jsonify
from flask import render_template
from flask_socketio import SocketIO, send, emit
from multiprocessing.connection import Client
import threading

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentparentdir = os.path.dirname(parentdir)
sys.path.append(parentparentdir)

from common.shared_state import SharedState

pixel_position_state = SharedState()
pixel_colour_state = SharedState()


def create_app(test_config=None):
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
        return jsonify(pixel_colour_state.get_if_available())

    @app.route('/position')
    def position():
        return jsonify(pixel_position_state.get_if_available())

    sock = SocketIO(app)

    @sock.on('colour')
    def colour():
        emit('colour', pixel_colour_state.get_if_available())

    return sock, app


if __name__ == '__main__':
    socketio, app = create_app()

    def create_client():
        try:
            with Client(('localhost', 6000)) as conn:
                while True:
                    [coords, colours] = conn.recv()
                    pixel_position_state.set(coords)
                    pixel_colour_state.set(colours)
        finally:
            conn.close()

    t = threading.Thread(target=create_client)
    t.setDaemon(True)
    t.start()

    socketio.run(app, host='0.0.0.0', port=5000)
