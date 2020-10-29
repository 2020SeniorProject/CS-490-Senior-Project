from threading import Lock
from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, emit 
import sqlite3
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

test_conn = create_connection("battle_sesh.db")
create_db_init(test_conn)

@app.route("/")
def index():
    return redirect(url_for('home'))

@app.route("/home")
def home():
    return render_template("base.html", async_mode=socketio.async_mode)
    
@app.route("/play")
def play():
    # conn = create_connection("battle_sesh.db")
    # create_db_init(conn)
    # create_db_log(conn)
    #To Do -> need to create way to add information to the DBs via the UI 
    # add_to_init(session_id, user_key, initiative)
    return render_template("index.html", async_mode=socketio.async_mode)


@socketio.on('set_initiative', namespace='/test')
def test_broadcast_message(message):
    conn = create_connection("battle_sesh.db")
    # Sends to all connected
    emit('initiative_update', {'data': message['data']}, broadcast=True)
    print(message['data'])
    add_to_init(conn, session_id, user_key, message['data'][0], message['data'][1])
    emit('log_update', {'data': "Initiative update"}, broadcast=True)


@socketio.on('send_chat', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    # emit('chat_update', {'data': message['data']}, broadcast=True)
    emit('chat_update', {'data': message['data']}, broadcast=True)
    emit('log_update', {'data': "Chat update"}, broadcast=True)


@socketio.on('connect', namespace='/test')
def test_connect():
    global initiative
    # Sends upon a new connection
    emit('log_update', {'data': "Connected"}, broadcast=True)
    conn = create_connection("battle_sesh.db")
    items = read_db(conn, "initiative", session_id)
    print(items)
    if items != []:
        emit('initiative_update', {'data': items})
        emit('log_update', {'data': "Initiative update"}, broadcast=True)