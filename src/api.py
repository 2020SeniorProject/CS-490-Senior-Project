import csv
import sqlite3

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

def get_races():
    rows = read_api_db("race")
    races_list = read_api_db("race", "race")

    races = set()
    for row in races_list:
        races.add(row[0])

    subraces = {}
    for race in races:
        subraces[race] = []
    for row in rows:
        subraces[row[0]].append(row[1])

    return races, subraces

def get_classes():
    rows = read_api_db("class")
    classes_list = read_api_db("class", "class")

    classes = set()
    for row in classes_list:
        classes.add(row[0])

    subclasses = {}
    for classs in classes:
        subclasses[classs] = []
    for row in rows:
        subclasses[row[0]].append(row[1])

    return classes, subclasses

# build_api_db(["race", "class"])
# read_db("race")
# read_db("class")

# print(get_races())
# print(get_classes())