from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit 

# Session works on a per-user basis - can't work to store values that multiple users need to access
# Will probably need to store in a database or something
initiative = []

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


@app.route("/")
def index():
    return render_template("index.html", async_mode=socketio.async_mode)

@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    global initiative
    # Sends to all connected
    emit('my_response', {'data': message['data']}, broadcast=True)
    initiative += message['data']


@socketio.on('connect', namespace='/test')
def test_connect():
    global initiative
    # Sends upon a new connection
    emit('my_response', {'data': "test"}, broadcast=True)
    if initiative != []:
        emit('my_response', {'data': initiative})