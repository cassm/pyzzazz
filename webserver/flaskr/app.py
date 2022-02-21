import os
import sys
import time
import inspect
import redis
import json
from flask import Flask
from flask import jsonify
from flask import render_template
from flask_socketio import SocketIO, emit

fps = 30

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_parent_dir)

r = redis.Redis(host='localhost', port=6379, db=0)


def get_colours():
    return json.loads(r.get('pyzzazz:leds:colours'))


app = Flask(__name__,
            static_folder='./static')

app.config.from_mapping(
    SECRET_KEY='dev'
)

try:
    os.makedirs(app.instance_path)
except OSError:
    pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/colour')
def colour():
    return jsonify(get_colours())


@app.route('/position')
def position():
    coords = json.loads(r.get('pyzzazz:leds:coords'))
    return jsonify(coords)


socketio = SocketIO(app)


@socketio.on('colours')
def sock_colour():
    emit('colours', get_colours())


def push_colours():
    while True:
        try:
            socketio.emit('colours', get_colours())
        except:
            break

        time.sleep(1.0 / fps)


@socketio.on('ready')
def colour_push():
    socketio.start_background_task(target=push_colours)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
