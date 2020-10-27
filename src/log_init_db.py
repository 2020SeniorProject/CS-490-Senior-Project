from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit 
import sqlite3



initiative = []


def create_db_log(conn):
    cur = conn.cursor()             #saves global ID key, user-specific key, and name of session/battle, DM Name, 
    cur.execute(f""" CREATE TABLE IF NOT EXISTS session_log (
                                        room_id TEXT PRIMARY KEY,
                                        user_key TEXT,
                                        title TEXT,     
                                        log LONGTEXT
                                    ); """)



def create_db_init(conn): #Takes session_id, User_key as main identifiers and then grabs order for the given session
    cur = conn.cursor()
    cur.execute(f""" CREATE TABLE IF NOT EXISTS initiative (
                                        room_id TEXT PRIMARY KEY,
                                        User_key TEXT,
                                        order TEXT NOT NULL
                                    ); """)    


def add_to_log(conn, session_id, user_key, title, log):
    cur = conn.cursor()
    print("adding to blog")
    sql = "INSERT INTO log(room_id, user_key, title, log)VALUES(?,?,?,?)"
    item = (session_id, user_key, title, log)
    cur.execute(sql, item)

def add_to_init(conn, session_id, user_key, order):
    cur = conn.cursor()
    sql = "INSERT INTO initiative(room_id, user_key, order)VALUES(?,?,?)"
    item = (session_id, user_key, order)
    cur.execute(sql, item)


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn


def read_db_init(conn, sesh_id, user_id):       #streamline these
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