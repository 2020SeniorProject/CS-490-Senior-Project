from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit 
import sqlite3



initiative = []

# Log table
# room_id = Global identifier for battle map created by user
# user_key = Unique user ID, allows for maps to be sorted by users
# title = ***CHANGED** used to name type of data being saved such as chat, action, connections etc.
# Log = entry from log, entered by users. Tracked to actions in battle and other relevant info
# timestamp = used to keep order of log entries for the room

def create_db_log(conn):
    cur = conn.cursor()              
    cur.execute(f""" CREATE TABLE IF NOT EXISTS log (
                                        room_id TEXT,
                                        user_key TEXT,
                                        title TEXT,     
                                        log LONGTEXT,
                                        timestamp DATETIME PRIMARY KEY
                                    ); """)



def add_to_log(conn, room_id, user_key, title, log, timestamp):
    cur = conn.cursor()
    sql = f"INSERT INTO log VALUES('{room_id}','{user_key}','{title}','{log}','{timestamp}');"
    # item = (room_id, user_key, title, log, timestamp)
    cur.execute(sql)
    conn.commit()
    # conn.close()



#initiative table
#room_id = Global identifier for battle map created by user
#user_key = Unique user ID, allows for maps to be sorted by users
#player_name = Entered by DM/map owner, player character name associated with the given intiative
#order = intiative # associated with a player
    # order allows for sorting

def create_db_init(conn): 
    cur = conn.cursor()
    cur.execute(f"""CREATE TABLE IF NOT EXISTS initiative 
                    (room_id TEXT PRIMARY KEY, user_key TEXT, player_name TEXT, init_val INT);""")    

def add_to_init(conn, room_id, user_key, player_name, init_val):
    cur = conn.cursor()
    sql = f"INSERT INTO initiative VALUES ('{room_id}', '{user_key}', '{player_name}', {init_val});"
    # item = (room_id, user_key, player_name, order)
    cur.execute(sql)
    conn.commit()
    # conn.close()


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn



## Selects player name and init # for reading
def read_db_init(conn, db_name, room_id):       #streamline these
    cur = conn.cursor() 
    init = []
    test = (room_id, )
    # for row in cur.execute(f"select * from {db_name} where session_id = {room_id}"):
    # for row in cur.execute(f"SELECT * FROM {db_name} where room_id = ?", test):
    for row in cur.execute(f"SELECT player_name, init_val FROM {db_name}"):
        init.append(row)
    return init



## Read chats from log_db
def read_db_log_chat(conn, db_name, room_id):       #streamline these
    cur = conn.cursor() 
    chat = []
    test = (room_id, )
    # for row in cur.execute(f"select * from {db_name} where session_id = {room_id}"):
    # for row in cur.execute(f"SELECT * FROM {db_name} where room_id = ?", test):
    for row in cur.execute(f"SELECT log FROM {db_name} where title = 'Chat'"):
        chat.append(row)
    return chat


