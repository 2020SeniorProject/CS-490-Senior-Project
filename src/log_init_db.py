from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit 
import sqlite3


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn


# Log table
# room_id = Global identifier for battle map created by user
# user_key = Unique user ID, allows for maps to be sorted by users
# title = ***CHANGED** used to name type of data being saved such as chat, action, connections etc.
# Log = entry from log, entered by users. Tracked to actions in battle and other relevant info
# timestamp = used to keep order of log entries for the room

#initiative table
#room_id = Global identifier for battle map created by user
#user_key = Unique user ID, allows for maps to be sorted by users
#player_name = Entered by DM/map owner, player character name associated with the given intiative
#order = intiative # associated with a player
    # order allows for sorting
  

def create_dbs():
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()              
        cur.execute(f"""CREATE TABLE IF NOT EXISTS log 
                        (row_id INT PRIMARY KEY, room_id TEXT,user_key TEXT, title TEXT, log LONGTEXT, timestamp DATETIME); """)

        cur.execute(f"""CREATE TABLE IF NOT EXISTS initiative 
                        (row_id INT PRIMARY KEY, room_id TEXT, user_key TEXT, player_name TEXT, init_val INT);""") 
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS users 
                        (user_id TEXT PRIMARY KEY, user_name TEXT NOT NULL, email TEXT NOT NULL, profile_pic TEXT);""") 



def add_to_db(db_name, values):
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        if db_name == "log":
            sql = f"INSERT INTO {db_name}(room_id, user_key, title, log, timestamp) VALUES('{values[0]}','{values[1]}','{values[2]}','{values[3]}','{values[4]}');"
        elif db_name == "init":
            sql = f"INSERT INTO initiative(room_id, user_key, player_name, init_val) VALUES ('{values[0]}', '{values[1]}', '{values[2]}', {values[3]});"
        elif db_name == "users":
            sql = f"INSERT INTO users(user_id, user_name, email, profile_pic) VALUES ('{values[0]}', '{values[1]}', '{values[2]}', '{values[3]}');"
        cur.execute(sql)
        conn.commit()


def read_db(db_name, rows="*", extra_clause = ""):
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        ret_lst = []
        for row in cur.execute(f"SELECT {rows} FROM {db_name} {extra_clause};"):
            ret_lst.append(row)
        return ret_lst