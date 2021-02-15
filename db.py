import sqlite3
import csv


# Global variable declarations
# These variables point towards the
# names of the database files.
global battle_sesh_db
global api_db
global error_db
battle_sesh_db = "battle_sesh.db"
api_db = "api.db"
error_db = "error.db"


def create_connection(db_file):
    """
    The create_connection function. This function
    was created to promote encapsulation and make
    code more readable. It simple creates and returns
    a connection to the specified database file.

    :param db_file:
        The name of the database file
        to which is being connected
    """
    conn = sqlite3.connect(db_file)
    return conn


# active_room table
# room_id = Global identifier for battle map created by user
# user_key = Unique user ID, allows for maps to be sorted by users
# chr_name = Entered by DM/map owner, player character name associated with the given intiative
# init_val = intiative # associated with a player
# is_turn = boolean stating whos turn it is - for any given room, only one entry will be 1 (true)
# char_token = String url of image to use for the character's token

# room_object 
# secret room ID # - incremental in the table
# User_key - ‘owner’ of the room, needed to lock out others from editing the room
# Name of room - what the owner of the room calls it (for visual purposes)
# Active room id - null if room not open, changes when room is ‘opened’ !!! THIS IS EQUIVALENT TO 'ROOM_ID IN chat, active_room, log, and characters !!!
# Map_status - stringified JSON representation of character tokens and locations on map. ex: { user_id: { username, character_name, character_image, room_id, height, width, top, left, is_turn } }
# Map URL - URL to the map (for the “background”)

# users table ****** THIS IS THE ONLY TABLE THAT UTILIZES USER_ID INSTEAD OF USER_KEY BUT THEY ARE SYNONYMOUS ******
# user_id = user_id gotten from Google 
# email = email address gotten from Google
# profile_pic = URL to Google profile pic
# username = username specific to our site. e.g. SirRunner
  
# characters table
# user_key = used to connect players to their created characters
# room_id = used to connect room_id to the room in which the character is playing
# chr_name, race, subclass, hitpoints = tracks character details and stats
# user_key and chr_name = primary keys to allow a character to be tracked across rooms and to allow repeats of character names across 

def create_dbs():
    """
    The create_dbs function. This function
    initializes the main database used by
    the application. The tables are as follows:

    :table log:
        row_id:     an autoincrementing primary key
                    Not truly necessary. Should be removed
        room_id:    the 8 alphanumeric key of the room
                    the log belongs to. Matches with
                    all other room_id rows in other tables.
        user_key:   the user ID we get from Google OAuth
                    of the user who generated the log.
                    Matches with all other user_id rows
                    in other tables. Should be renamed
                    user_id
        title:      Deprecated. Should be removed.
        log:        The actual log message generated
                    by the application during runtime.
        timestamp:  The time the log was generated.
    :table chat:
        row_id:     an autoincrementing primary key.
                    Not truly necessary. Should be removed
        room_id:    the 8 alphanumeric key of the room
                    the log belongs to. Matches with
                    all other room_id rows in other tables.
        user_key:   the user ID we get from Google OAuth
                    of the user who sent the chat.
                    Matches with all other user_id rows
                    in other tables. Should be renamed
                    user_id
        chr_name:   Name of the character? Not all too sure 
                    without further testing. It may be the user's
                    username. In either case, it is unused and
                    should be removed
        chat:       The actual chat sent by the user
        timestamp:  The time the chat was received by
                    the backend.
    :table active_room:
        room_id:    the 8 alphanumeric key of the room
                    the log belongs to. Matches with
                    all other room_id rows in other tables.
        user_key:   the user ID we get from Google OAuth
                    of the user who sent the chat.
                    Matches with all other user_id rows
                    in other tables. Should be renamed
                    user_id
        chr_name:   The name of the user's character
                    in the room. Matches with all other
                    character_name rows. Should be renamed
                    character_name
        init_val:   The initiative value of the character
        is_turn:    Boolean value stating if it is that
                    character's turn.
        char_token: The URL to the character's battlemap image.
    :table room_object:
    :table users:
    :table characters:
    """
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS log 
                        (row_id INT PRIMARY KEY, room_id TEXT, user_key TEXT, title TEXT, log LONGTEXT, timestamp DATETIME); """)
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS chat
                        (row_id INT PRIMARY KEY, room_id TEXT, user_key TEXT, chr_name TEXT, chat TEXT, timestamp DATETIME);""")
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS active_room 
                        (room_id TEXT, user_key TEXT, chr_name TEXT, init_val INT, is_turn INT, char_token TEXT, PRIMARY KEY(room_id, user_key, chr_name));""") 

        cur.execute(f"""CREATE TABLE IF NOT EXISTS room_object
                        (row_id INTEGER PRIMARY KEY, user_key TEXT, room_name TEXT, active_room_id TEXT, map_status TEXT, map_url TEXT, dm_notes TEXT);""")
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS users 
                        (user_id TEXT PRIMARY KEY, email TEXT NOT NULL, profile_pic TEXT, username Text);""") 

        cur.execute(f""" CREATE TABLE IF NOT EXISTS characters
                            (user_key TEXT, chr_name TEXT, class TEXT, subclass TEXT, race TEXT, subrace TEXT, speed INT, level INT, strength INT, dexterity INT, constitution INT, intelligence INT, wisdom INT, charisma INT, hitpoints INT, char_token TEXT, PRIMARY KEY(user_key, chr_name));""")
        

def add_to_db(table_name, values):
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        if table_name == "log":
            cur.execute("INSERT INTO log(room_id, user_key, title, log, timestamp) VALUES(?, ?, ?, ?, ?)", values)
        elif table_name == "chat":
            cur.execute("INSERT INTO chat(room_id, user_key, chr_name, chat, timestamp) VALUES(?, ?, ?, ?, ?)", values)
        elif table_name == "active_room":
            cur.execute("INSERT INTO active_room(room_id, user_key, chr_name, init_val, is_turn, char_token) VALUES(?, ?, ?, ?, ?, ?)", values)
        elif table_name == "room_object":
            cur.execute("INSERT INTO room_object(user_key, room_name, active_room_id, map_status, map_url, dm_notes) VALUES(?,?,?,?,?,?)", values)
        elif table_name == "chars":
            cur.execute("""INSERT INTO characters(user_key, chr_name, class, subclass, race, subrace, speed, level, strength, dexterity, constitution, intelligence, wisdom, charisma, hitpoints, char_token) 
                           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
        elif table_name == "users":
            cur.execute("INSERT INTO users(user_id, email, profile_pic, username) VALUES (?, ?, ?, ?)", values)
        conn.commit()


def read_db(table_name, rows="*", extra_clause = "", read_api_db=False):
    if read_api_db:
        db_to_read_from = api_db
    else:
        db_to_read_from = battle_sesh_db
    with create_connection(db_to_read_from) as conn:
        cur = conn.cursor()
        ret_lst = []
        for row in cur.execute(f"SELECT {rows} FROM {table_name} {extra_clause};"):
            ret_lst.append(row)
        return ret_lst


def delete_from_db(table_name, extra_clause = ""):
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table_name} {extra_clause};")
        conn.commit()

def reset_db(table_name):
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"""DROP TABLE IF EXISTS {table_name};""")
        conn.commit()

        create_dbs()

def update_db(table_name, columns_values, extra_clause):
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"""UPDATE {table_name} SET {columns_values} {extra_clause};""")
        conn.commit()


def build_api_db(files):

    def decomment(csvfile):
        for row in csvfile:
            raw = row.split('#')[0].strip()
            if raw: yield raw

    with sqlite3.connect(api_db) as conn:
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
                reader = csv.reader(decomment(f))
                if file == "race":
                    for row in reader:
                        cur.execute(f"""INSERT INTO race(race, subrace, speed) VALUES(?,?,?);""", row)
                elif file == "class":
                    for row in reader:
                        cur.execute(f"""INSERT INTO class(class, subclass) VALUES(?,?);""", row)
        conn.commit()


def get_api_info(table, row):
    rows = read_db(table, read_api_db=True)
    main_column = read_db(table, row, read_api_db=True)

    main_column_set = set()
    for row in main_column:
        main_column_set.add(row[0])
    
    column_subsets = {}
    for column in main_column_set:
        column_subsets[column] = []
    for row in rows:
        column_subsets[row[0]].append(row[1])

    return main_column_set, column_subsets


def build_error_db():
    with create_connection(error_db) as conn:
        cur = conn.cursor()              
        cur.execute(f"""CREATE TABLE IF NOT EXISTS error 
                        (row_id INT PRIMARY KEY, error_desc TEXT); """)

def add_to_error_db(values):
    with create_connection(error_db) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO error(error_desc) VALUES(?)", (values,))
        conn.commit()
    
def read_error_db():
    with create_connection(error_db) as conn:
        cur = conn.cursor()
        ret_lst = []
        for row in cur.execute(f"SELECT * FROM error;"):
            ret_lst.append(row)
        return ret_lst