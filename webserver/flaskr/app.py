import os
import sys
import time
import inspect
from flask import Flask
from flask import jsonify
from flask import render_template
from flask_socketio import SocketIO, send, emit
from multiprocessing import shared_memory
import threading

fps = 30

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_parent_dir)

from common.shared_state import SharedState

avail_cmd_state = SharedState()

shm_colours = shared_memory.SharedMemory(name='shm_pyzzazz_colours')
shm_coords = shared_memory.ShareableList(name='shm_pyzzazz_coords')


def get_colours():
    col = list(shm_colours.buf)
    return [col[i:i + 3] for i in range(0, len(col), 3)]


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
    coords = list(shm_coords)
    return jsonify([coords[i:i + 3] for i in range(0, len(coords), 3)])


# @app.route('/avail_cmds')
# def avail_cmds():
#     return jsonify(avail_cmd_state.get_if_available())

socketio = SocketIO(app)


@socketio.on('colours')
def sock_colour():
    emit('colours', get_colours())


@socketio.on('avail_cmds')
def sock_avail_cmds():
    emit('avail_cmds', avail_cmd_state.get_if_available())


def push_colours():
    while True:
        try:
            socketio.emit('colours', get_colours())
        except:
            break

        time.sleep(1.0 / fps)


@socketio.on('ready')
def colour_push():
    col_thread = threading.Thread(target=push_colours)
    col_thread.setDaemon(True)
    col_thread.start()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
