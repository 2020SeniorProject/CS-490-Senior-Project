from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit 
import sqlite3

# Log table
# room_id = Global identifier for battle map created by user
# user_key = Unique user ID, allows for maps to be sorted by users
# title = ***CHANGED** used to name type of data being saved such as chat, action, connections etc.
# Log = entry from log, entered by users. Tracked to actions in battle and other relevant info
# timestamp = used to keep order of log entries for the room

def create_db_log():
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()              
        cur.execute(f"""CREATE TABLE IF NOT EXISTS log 
                        (row_id INT PRIMARY KEY, room_id TEXT,user_key TEXT, title TEXT, log LONGTEXT, timestamp DATETIME); """)


def add_to_log(room_id, user_key, title, log, timestamp):
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        sql = f"INSERT INTO log(room_id, user_key, title, log, timestamp) VALUES('{room_id}','{user_key}','{title}','{log}','{timestamp}');"
        cur.execute(sql)
        conn.commit()


#initiative table
#room_id = Global identifier for battle map created by user
#user_key = Unique user ID, allows for maps to be sorted by users
#player_name = Entered by DM/map owner, player character name associated with the given intiative
#order = intiative # associated with a player
    # order allows for sorting

def create_db_init(): 
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS initiative 
                        (row_id INT PRIMARY KEY, room_id TEXT, user_key TEXT, player_name TEXT, init_val INT);""")    

def add_to_init(room_id, user_key, player_name, init_val):
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        sql = f"INSERT INTO initiative(room_id, user_key, player_name, init_val) VALUES ('{room_id}', '{user_key}', '{player_name}', {init_val});"
        cur.execute(sql)
        conn.commit()


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn



## Selects player name and init # for reading
def read_db_init(db_name, room_id):       #streamline these
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor() 
        init = []
        for row in cur.execute(f"SELECT player_name, init_val FROM {db_name}"):
            init.append(row)
        return init



## Read chats from log_db
def read_db_log_chat(db_name, room_id):       #streamline these
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor() 
        chat = []
        for row in cur.execute(f"SELECT log FROM {db_name} where title = 'Chat'"):
            chat.append(row)
        return chat


