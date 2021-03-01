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


# characters table
# user_id = used to connect players to their created characters
# room_id = used to connect room_id to the room in which the character is playing
# character_name, race, subclass, hitpoints = tracks character details and stats
# user_id and character_name = primary keys to allow a character to be tracked across rooms and to allow repeats of character names across 

def create_dbs():
    """
    The create_dbs function. This function
    initializes the main database used by
    the application. The tables are as follows:

    :table log:
        row_id:         an autoincrementing primary key
        room_id:        the 8 alphanumeric key of the room
                        the log belongs to. Matches with
                        all other room_id rows in other tables.
        user_id:        the user ID we get from Google OAuth
                        of the user who generated the log.
                        Matches with all other user_id rows
                        in other tables.
        title:          Deprecated. Should be removed.
        log:            The actual log message generated
                        by the application during runtime.
        timestamp:      The time the log was generated.
    :table chat:
        row_id:         an autoincrementing primary key.
        room_id:        the 8 alphanumeric key of the room
                        the log belongs to. Matches with
                        all other room_id rows in other tables.
        user_id:        the user ID we get from Google OAuth
                        of the user who sent the chat.
                        Matches with all other user_id rows
                        in other tables.
        character_name: Name of the character? Not all too sure 
                        without further testing. It may be the user's
                        username. In either case, it appears is unused and
                        should be removed
        chat:           The actual chat sent by the user
        timestamp:      The time the chat was received by
                        the backend.
    :table active_room:
        room_id:        the 8 alphanumeric key of the room
                        the log belongs to. Matches with
                        all other room_id rows in other tables.
        user_id:        the user ID we get from Google OAuth
                        of the user who owns the characters.
                        Matches with all other user_id rows
                        in other tables.
        character_name: The name of the user's character
                        in the room. Matches with all other
                        character_name rows.
        init_val:       The initiative value of the character
        is_turn:        Boolean value stating if it is that
                        character's turn.
        char_token:     The URL to the character's battlemap image.
                        Should be renamed character_token
    :table room_object:
        row_id:         an autoincrementing primary key.
                        Is hidden from all users except
                        the owner of a room.
        user_id:        the user ID we get from Google OAuth
                        of the user who owns the room.
                        Matches with all other user_id rows
                        in other tables.
        character_name: Honestly, doesn't look like this does
                        anything. Should be removed.
        room_name:      String name of the room
        active_room_id: String name of the active rooms that
                        use this template. Currently only holds
                        a string. Should be updated to hold a
                        jsonified list of active room ids.
        map_status:     Jsonified dictionary of dictionares of
                        character information in the room. Is
                        structured as follows:
                        {"user_id": {"username": username, "character_name": character_name
                        "room_id": room_id, "character_image": character_token URL,
                        "height": height, "width": width, "top": top pixel location,
                        "left": left pixel location, "is_turn": 0 or 1 Boolean}}
        map_url:        URL of the battle map used by the room
        dm_notes:       The DM Notes entered by the user. Can be
                        updated by editing the room.
    :table users:
        user_id:        the user ID we get from Google OAuth.
                        Matches with all other user_id rows
                        in other tables.
        email:          the email we get from Google OAuth
        profile_pic:    the URL to the Google profile
                        picture we recieve from Google
                        OAuth. Should be renamed profile_picture
        username:       the username of the user on the
                        application. Must be unique across all
                        users. Can be updated via the settings page.
                        On the backend, the username
                        or user_id can be used to identify users.
                        However, on the front end, only the username
                        should be used.
    :table characters:
        user_id:        the user ID we get from Google OAuth
                        of the user who owns the character.
                        Matches with all other user_id rows
                        in other tables.
        character_name: the name of the character. Matches
                        with all other character_name rows
        class:          the class of the character. Not truly
                        used at the moment. Is being collected
                        for future use.
        subclass:       the subclass of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        race:           the race of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        subrace:        the subrace of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        speed:          the speed of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        level:          the level of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        strength:       the strength stat of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        dexterity:      the dexterity stat of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        constitution:   the constitution stat of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        intelligence:   the intelligence stat of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        wisdom:         the wisdom stat of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        charisma:       the charisma stat of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        hitpoints:      the hitpoints of the character. Not truly
                        used at the moment. Is being collected for
                        future use.
        char_token:     the URL of the character's battlemap image.
                        Matches with all other character_token rows.
                        Should be renamed char_token.
    """
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS log 
                        (row_id INT PRIMARY KEY, room_id TEXT, user_id TEXT, title TEXT, log LONGTEXT, timestamp DATETIME); """)
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS chat
                        (row_id INT PRIMARY KEY, room_id TEXT, user_id TEXT, character_name TEXT, chat TEXT, timestamp DATETIME);""")
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS active_room 
                        (room_id TEXT, user_id TEXT, character_name TEXT, init_val INT, is_turn INT, char_token TEXT, PRIMARY KEY(room_id, user_id, character_name));""") 

        cur.execute(f"""CREATE TABLE IF NOT EXISTS room_object
                        (row_id INTEGER PRIMARY KEY, user_id TEXT, room_name TEXT, active_room_id TEXT, map_status TEXT, map_url TEXT, dm_notes TEXT);""")
        
        cur.execute(f"""CREATE TABLE IF NOT EXISTS users 
                        (user_id TEXT PRIMARY KEY, email TEXT NOT NULL, profile_pic TEXT, username Text);""") 

        cur.execute(f""" CREATE TABLE IF NOT EXISTS characters
                            (user_id TEXT, character_name TEXT, class TEXT, subclass TEXT, race TEXT, subrace TEXT, speed INT, level INT, strength INT, dexterity INT, constitution INT, intelligence INT, wisdom INT, charisma INT, hitpoints INT, char_token TEXT, PRIMARY KEY(user_id, character_name));""")
        

def add_to_db(table_name, values):
    """
    The add_to_db function. This function
    adds a row to the specified table. This
    is only used on the battle_sesh_db. Adding
    to the error db should use add_to_error_db.

    :param table_name:
        The name of the table to which
        is being appended
    :param values:
        The data values that are being
        appended to the row. Comes in
        as a tuple in the correct order
    """
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        if table_name == "log":
            cur.execute("INSERT INTO log(room_id, user_id, title, log, timestamp) VALUES(?, ?, ?, ?, ?)", values)
        elif table_name == "chat":
            cur.execute("INSERT INTO chat(room_id, user_id, character_name, chat, timestamp) VALUES(?, ?, ?, ?, ?)", values)
        elif table_name == "active_room":
            cur.execute("INSERT INTO active_room(room_id, user_id, character_name, init_val, is_turn, char_token) VALUES(?, ?, ?, ?, ?, ?)", values)
        elif table_name == "room_object":
            cur.execute("INSERT INTO room_object(user_id, room_name, active_room_id, map_status, map_url, dm_notes) VALUES(?,?,?,?,?,?)", values)
        elif table_name == "chars":
            cur.execute("""INSERT INTO characters(user_id, character_name, class, subclass, race, subrace, speed, level, strength, dexterity, constitution, intelligence, wisdom, charisma, hitpoints, char_token) 
                           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
        elif table_name == "users":
            cur.execute("INSERT INTO users(user_id, email, profile_pic, username) VALUES (?, ?, ?, ?)", values)
        conn.commit()


def read_db(table_name, rows="*", extra_clause = "", read_api_db=False):
    """
    The read_db function. This function
    reads all specified rows of a table.

    :param table_name:
        the name of the table being accessed
    :param rows:
        the row names being accessed. Defaults to
        "*": all of the rows
    :param extra_clause:
        any sort of extra filter that may be used in
        an SQL query. E.G. "WHERE user_id = '0304920349'"
        Defaults to the empty string
    :read_api_db:
        a Boolean variable stating if the api db is being accessed.
        If true, the api db is accessed. Otherwise, the battle
        session db is accessed.
    """
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
    """
    The delete_from_db function. This function
    deletes rows with the specified information.

    :param table_name:
        The name of the table in the battle_sesh
        db. This is the only db that can be accessed
        from this function
    :param extra_clause:
        Any extraneous part of a delete query beyond
        "DELETE FROM table_name". This parameter filters
        the specific rows to its defines.
    """
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table_name} {extra_clause};")
        conn.commit()

def reset_db(table_name):
    """
    The reset_db function. This function drops a
    table and then calls the create_dbs() function
    in order to recreate it.

    :param table_name:
        The name of the table that is going
        to be reset.
    """
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"""DROP TABLE IF EXISTS {table_name};""")
        conn.commit()

        create_dbs()

def update_db(table_name, columns_values, extra_clause):
    """
    The update_db function. This function updates the
    specified rows with the new values.

    :param table_name:
        The name of the table that is being accessed
    :param columns_values:
        The columns and their new values
    :param extra_clause:
        The final part of the SQL query where the
        specific rows are filtered to.
    """
    with create_connection(battle_sesh_db) as conn:
        cur = conn.cursor()
        cur.execute(f"""UPDATE {table_name} SET {columns_values} {extra_clause};""")
        conn.commit()


def build_api_db(files):
    """
    The build_api_db function. This function
    builds the api tables based upon the files
    that it is given.

    :param files:
        A list of the files that are used
        to build the api tables.
    """

    def decomment(csvfile):
        """
        The decomment function. This function is only
        accessible by the build_api_db function to strip
        off comments written in the given csv files.

        Comments are denotated by a hashtag (#) until a newline.

        :param csvfile:
            The name of the csv file
        """
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
    """
    The get_api_info function. This function retrieves all of the
    data from the specified api table.

    :param table:
        The name of the api table being accessed.
    :param row:
        The name of the main row in the table. Most likely
        matches the table name.

    Should rename either the paramater row or the iterator row
    """
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
    """
    The build_error_db function. This function
    builds the error db.

    Isn't really used. Ever. Should be removed.
    """
    with create_connection(error_db) as conn:
        cur = conn.cursor()              
        cur.execute(f"""CREATE TABLE IF NOT EXISTS error 
                        (row_id INT PRIMARY KEY, error_desc TEXT); """)

def add_to_error_db(values):
    """
    The add_to_error_db. This function adds
    data to the error db.

    Isn't really used. Ever. Should be removed.

    :param values:
        A tuple of the values that get put into 
        the error db.
    """
    with create_connection(error_db) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO error(error_desc) VALUES(?)", (values,))
        conn.commit()
    
def read_error_db():
    """
    The read_error_db function. This function
    reads the error db.

    Isn't really used. Ever. Should be removed.
    """
    with create_connection(error_db) as conn:
        cur = conn.cursor()
        ret_lst = []
        for row in cur.execute(f"SELECT * FROM error;"):
            ret_lst.append(row)
        return ret_lst