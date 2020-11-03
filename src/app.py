from threading import Lock
from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, emit 
import sqlite3
import datetime
from log_init_db import *

# Session works on a per-user basis - can't work to store values that multiple users need to access

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

session_id = "69BBEG69" #placeholder till we figure out id creation method, use usernames with random numbers?
user_key = "BigGamer420" #placeholder till we create some sort of user database?

create_dbs()

@app.route("/")
def index():
    return redirect(url_for('home'))

@app.route("/home")
def home():
    return render_template("base.html", async_mode=socketio.async_mode)
    
@app.route("/play")
def play():
    return render_template("index.html", async_mode=socketio.async_mode)


@socketio.on('set_initiative', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    emit('initiative_update', {'data': message['data']}, broadcast=True)
    emit('log_update', {'data': "Initiative Added"}, broadcast=True)

    add_to_db("init", (session_id, user_key, message['data'][0], message['data'][1]))
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    init_name = message['data'][0] + message['data'][1]
    add_to_db("log", (session_id, user_key, "Init", init_name, s) )

@socketio.on('send_chat', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    emit('chat_update', {'data': message['data']}, broadcast=True)
    emit('log_update', {'data': "Chat update"}, broadcast=True)

    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    add_to_db("log", (session_id, user_key, "Chat", message['data'][0], s))

@socketio.on('connect', namespace='/test')
def test_connect():
    # Sends upon a new connection
    emit('log_update', {'data': "Connected"}, broadcast=True)

    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    add_to_db("log", (session_id, user_key, "Connection", "User connected", s))

    init_items = read_db("initiative", "player_name, init_val")
    chat_items = read_db("log", "log", "where title = 'Chat'")

    if init_items != []:
        for item in init_items:
            emit('initiative_update', {'data': item})
            
        emit('log_update', {'data': "Initiative List Received"}, broadcast=True)
    if chat_items != []:
        for item in chat_items:
            emit('chat_update', {'data': item})
            
        emit('log_update', {'data': "Chat List Received"}, broadcast=True)