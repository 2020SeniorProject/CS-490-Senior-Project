from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit 
import sqlite3

# Session works on a per-user basis - can't work to store values that multiple users need to access
# Will probably need to store in a database or something
initiative = []

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def create_db_log(conn):
    cur = conn.cursor()             #saves global ID key, user-specific key, and name of session/battle, DM Name, 
    cur.execute(f""" CREATE TABLE IF NOT EXISTS session_log (
                                        session_id TEXT PRIMARY KEY,
                                        user_key TEXT,
                                        title TEXT,     
                                        log LONGTEXT
                                    ); """)



def create_db_init(conn): #Takes session_id, User_key as main identifiers and then grabs order for the given session
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS initiative (
                                        session_id TEXT PRIMARY KEY,
                                        User_key TEXT,
                                        order TEXT NOT NULL
                                    ); """)    


def add_to_log(conn, session_id, user_key, title, log):
    cur = conn.cursor()
    print("adding to blog")
    sql = "INSERT INTO log(session_id, user_key, title, log)VALUES(?,?,?,?)"
    item = (session_id, user_key, title, log)
    cur.execute(sql, item)

def add_to_init(conn, session_id, user_key, order):
    cur = conn.cursor()
    sql = "INSERT INTO initiative(session_id, user_key, order)VALUES(?,?,?)"
    item = (session_id, user_key, order)
    cur.execute(sql, item)


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn


def read_db_init(conn, sesh_id, user_id):
    cur = conn.cursor() 
    init = []
    for row in cur.execute(f"select order from init where session_id = {sesh_id}"):
        init.append(row)
    return init



def read_db_log(conn, sesh_id, user_id):
    cur = conn.cursor() 
    log = []
    for row in cur.execute(f"select log from sesshion_log where session_id = {sesh_id}"):
        log.append(row)
    return log



@app.route("/")
def index():
    conn = create_connection("battle_sesh.db")
    create_db_init(conn)
    create_db_log(conn)
    session_id = "69BBEG69" #placeholder till we figure out id creation method, use usernames with random numbers?
    user_key = "BigGamer420" #placeholder till we create some sort of user database?
    #To Do -> need to create way to add information to the DBs via the UI 
    # add_to_init(session_id, user_key, initiative)
    return render_template("index.html", async_mode=socketio.async_mode)


@socketio.on('set_initiative', namespace='/test')
def test_broadcast_message(message):
    global initiative
    # Sends to all connected
    emit('initiative_update', {'data': message['data']}, broadcast=True)
    initiative += message['data']
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
    if initiative != []:
        emit('initiative_update', {'data': initiative})
        emit('log_update', {'data': "Initiative update"}, broadcast=True)