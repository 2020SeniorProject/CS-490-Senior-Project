import sqlite3

# Needed for API
import csv

# TODO: Combine API db and battle_sesh db functions together

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn


# log table
# room_id = Global identifier for battle map created by user
# user_key = Unique user ID, allows for maps to be sorted by users
# title = ***CHANGED** used to name type of data being saved such as chat, action, connections etc.
# Log = entry from log, entered by users. Tracked to actions in battle and other relevant info
# timestamp = used to keep order of log entries for the room

# initiative table
# room_id = Global identifier for battle map created by user
# user_key = Unique user ID, allows for maps to be sorted by users
# player_name = Entered by DM/map owner, player character name associated with the given intiative
# init_val = intiative # associated with a player

# users table
# user_id = user_id gotten from Google
# user_name = username gotten from Google
# email = email address gotten from Google
# profile_pic = URL to Google profile pic
  
# characters table
# user_key = used to connect players to their created characters
# room_id = used to connect room_id to the room in which the character is playing
# chr_name, race, subclass, hitpoints = tracks character details and stats
# user_key and chr_name = primary keys to allow a character to be tracked across rooms and to allow repeats of character names across 

def create_dbs():
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()              
        cur.execute(f"""CREATE TABLE IF NOT EXISTS log 
                        (row_id INT PRIMARY KEY, room_id TEXT,user_key TEXT, title TEXT, log LONGTEXT, timestamp DATETIME); """)

        cur.execute(f"""CREATE TABLE IF NOT EXISTS initiative 
                        (row_id INT PRIMARY KEY, room_id TEXT, user_key TEXT, player_name TEXT, init_val INT);""") 
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS users 
                        (user_id TEXT PRIMARY KEY, user_name TEXT NOT NULL, email TEXT NOT NULL, profile_pic TEXT);""") 

        cur.execute(f""" CREATE TABLE IF NOT EXISTS characters
                            (user_id TEXT, room_id TEXT, chr_name TEXT, class TEXT, subclass TEXT, race TEXT, hitpoints INT, PRIMARY KEY(user_id, chr_name));""")


def add_to_db(db_name, values):
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        if db_name == "log":
            sql = f"INSERT INTO {db_name}(room_id, user_key, title, log, timestamp) VALUES('{values[0]}','{values[1]}','{values[2]}','{values[3]}','{values[4]}');"
        elif db_name == "init":
            sql = f"INSERT INTO initiative(room_id, user_key, player_name, init_val) VALUES ('{values[0]}', '{values[1]}', '{values[2]}', {values[3]});"
        elif db_name == "chars":
            sql = f"INSERT INTO characters(user_id, room_id, chr_name, class, subclass, race, hitpoints) VALUES('{values[0]}', '{values[1]}', '{values[2]}', '{values[3]}', '{values[4]}', '{values[5]}', {values[6]});"
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


def delete_from_db(db_name, extra_clause = ""):
    with create_connection("battle_sesh.db") as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {db_name} {extra_clause};")
        conn.commit()


def build_api_db(files):
    with sqlite3.connect("api.db") as conn:
        cur = conn.cursor()

        for file in files:
            cur.execute(f"""DROP TABLE IF EXISTS {file};""")
            if file == "race":
                cur.execute(f"""CREATE TABLE IF NOT EXISTS race 
                                (race TEXT NOT NULL, subrace TEXT NOT NULL, speed INT, PRIMARY KEY (race, subrace)); """)
            elif file == "class":
                cur.execute(f"""CREATE TABLE IF NOT EXISTS class
                                (class TEXT NOT NULL, subclass TEXT NOT NULL, PRIMARY KEY (class, subclass));""")
            with open(f"data_files/{file}.csv", 'r') as f:
                reader = csv.reader(f)
                if file == "race":
                    for row in reader:
                        cur.execute(f"""INSERT INTO race(race, subrace, speed) VALUES('{row[0]}', '{row[1]}', '{row[2]}');""")
                elif file == "class":
                    for row in reader:
                        cur.execute(f"""INSERT INTO class(class, subclass) VALUES('{row[0]}', '{row[1]}');""")
        conn.commit()


def read_api_db(db_name, rows="*", extra_clause = ""):
    with sqlite3.connect("api.db") as conn:
        cur = conn.cursor()
        ret_lst = []
        for row in cur.execute(f"SELECT {rows} FROM {db_name} {extra_clause};"):
            ret_lst.append(row)
        # print(ret_lst)
        return ret_lst


def get_api_info(table, row):
    rows = read_api_db(table)
    main_column = read_api_db(table, row)

    main_column_set = set()
    for row in main_column:
        main_column_set.add(row[0])
    
    column_subsets = {}
    for column in main_column_set:
        column_subsets[column] = []
    for row in rows:
        column_subsets[row[0]].append(row[1])

    return main_column_set, column_subsets