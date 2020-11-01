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

test_conn = create_connection("battle_sesh.db")
create_db_init(test_conn)
create_db_log(test_conn)

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
    add_to_init(conn, session_id, user_key, message['data'][0], message['data'][1])
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    init_name = message['data'][0] + message['data'][1]
    add_to_log(conn, session_id, user_key, "Init", init_name, s)   #redundant??
    emit('log_update', {'data': "Initiative update"}, broadcast=True)


@socketio.on('send_chat', namespace='/test')
def test_broadcast_message(message):
    # Sends to all connected
    # emit('chat_update', {'data': message['data']}, broadcast=True)
    conn = create_connection("battle_sesh.db")
    emit('chat_update', {'data': message['data']}, broadcast=True)
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    add_to_log(conn, session_id, user_key, "Chat", message['data'][0], s)
    emit('log_update', {'data': "Chat update"}, broadcast=True)


@socketio.on('connect', namespace='/test')
def test_connect():
    global initiative
    # Sends upon a new connection
    conn = create_connection("battle_sesh.db")
    emit('log_update', {'data': "Connected"}, broadcast=True)
    s = datetime.datetime.now().isoformat(sep=' ',timespec='seconds')
    add_to_log(conn, session_id, user_key, "Connection", "User connected", s)
    init_items = read_db_init(conn, "initiative", session_id)
    chat_items = read_db_log_chat(conn, "log", session_id)
    # print(init_items)
    # print(chat_items[0][0])
    if init_items != []:
        emit('initiative_update', {'data': init_items})
        emit('log_update', {'data': "Initiative update"}, broadcast=True)
    if chat_items != []:
        emit('chat_update', {'data': chat_items})
        emit('log_update', {'data': "Chat Update"}, broadcast=True)