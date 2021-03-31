# third parties
import pytest
import flask_login 
import flask
from flask import Flask, session
from flask.testing import FlaskClient as BaseFlaskClient
from flask_login import current_user, UserMixin
from flask_wtf.csrf import generate_csrf
from flask_socketio import SocketIO, emit, join_room, close_room, rooms
from requests import get, post, request
import sqlite3

# python library imports
import toml
import pathlib
import os, sys
import tempfile
from unittest import mock


# https://flask.palletsprojects.com/en/1.1.x/testing/
# Internal imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app, socketio
from app import determine_if_user_spamming
from db import create_dbs, add_to_db, delete_from_db, read_db
from db import *
import wtforms.csrf 
from classes import User, AnonymousUser


# 
#  TO AVOID DEPRECATION WARNING FROM OUR 3rd PARTY LIBRARIES 
#  I RECOMMEND USING THE COMMAND 
#  python3 -m pytest tests/test_app.py -W ignore::DeprecationWarning
#  
#  Use this command to find coverage calculation
#  python3 -m pytest --cov=. tests/ -W ignore::DeprecationWarning
#

def get_cases(category: str):
    with open(pathlib.Path(__file__).with_suffix(".toml")) as f:
        all_cases = toml.load(f)
        for case in all_cases[category]:
            if case.get("fields"):
                yield (case.get("fields"), case.get("inputs"), case.get("expected"))
            else:
                yield (case.get("inputs"), case.get("expected"))
                


class RequestShim(object):
    """
    A fake request that proxies cookie-related methods to a Flask test client.
    """
    def __init__(self, client):
        self.client = client
        self.vary = set({})

    def set_cookie(self, key, value='', *args, **kwargs):
        "Set the cookie on the Flask test client."
        server_name = flask.current_app.config["SERVER_NAME"] or "localhost"
        return self.client.set_cookie(
            server_name, key=key, value=value, *args, **kwargs
        )

    def delete_cookie(self, key, *args, **kwargs):
        "Delete the cookie on the Flask test client."
        server_name = flask.current_app.config["SERVER_NAME"] or "localhost"
        return self.client.delete_cookie(
            server_name, key=key, *args, **kwargs
        )

# We're going to extend Flask's built-in test client class, so that it knows
# how to look up CSRF tokens for you!
class FlaskClient(BaseFlaskClient):
    @property
    def csrf_token(self):
        # First, we'll wrap our request shim around the test client, so that
        # it will work correctly when Flask asks it to set a cookie.
        request = RequestShim(self) 
        # Next, we need to look up any cookies that might already exist on
        # this test client, such as the secure cookie that powers `flask.session`,
        # and make a test request context that has those cookies in it.
        environ_overrides = {}
        self.cookie_jar.inject_wsgi(environ_overrides)
        with flask.current_app.test_request_context(
                "/login", environ_overrides=environ_overrides,
            ):
            # Now, we call Flask-WTF's method of generating a CSRF token...
            csrf_token = generate_csrf()
            # ...which also sets a value in `flask.session`, so we need to
            # ask Flask to save that value to the cookie jar in the test
            # client. This is where we actually use that request shim we made! 
            flask.current_app.save_session(flask.session, request)
            # And finally, return that CSRF token we got from Flask-WTF.
            return csrf_token


# 
# SQL Tests
# 


def test_sql_db_connect():

    battle_db_con = create_connection("battle_sesh.db")
    battle_cursor = battle_db_con.cursor()

    assert battle_cursor.execute("""SELECT * from log, 
                                                chat,
                                                active_room, 
                                                room_object,
                                                users, 
                                                characters""")  














# Testing client with authenticated user 
# but nothing else in the db except another User named Charnk(for site name test)
@pytest.fixture
def client_1(mocker):
    app.config['TESTING'] = True
    app.test_client_class = FlaskClient
    add_to_db("users", ("6969testingCharnky", "treach01@luther.edu", "mock.jpg", "Charnk98"))
    with app.test_client() as client_1:
        create_dbs()
        mocker.patch("flask_login.utils._get_user", return_value = User("mocksterid", "mail", "mock.jpg", "mrMock420"))
        add_to_db("users", ("mocksterid", "mail", "mock.jpg", "mrMock420"))
        yield client_1
    
    delete_from_db("users", "WHERE username = 'Charnk98'")
    delete_from_db("users", "WHERE user_id = 'mocksterid'")
    delete_from_db("room_object", "WHERE user_id = 'mocksterid'")
    delete_from_db("characters", "WHERE user_id = 'mocksterid'")







#User with a character in the DB and 
# a room in it for socketio testing
@pytest.fixture
def client_2(mocker):
    app.config['TESTING'] = True
    app.test_client_class = FlaskClient
    with app.test_client() as client_2:
        create_dbs()
        mocker.patch("flask_login.utils._get_user", return_value = User("paulinaMock21", "mail", "mock.jpg", "mrsmock69"))
        add_to_db("room_object", ("paulinaMock21", "Dungeon Battle", "ABC123", "", "this_is_sweet_map.jpg", "This is going to be an intense batle"))
        add_to_db("active_room", ("ABC123", "paulinaMock21", "Yanko", 10, 0, "yanko.jpg"))
        add_to_db("users", ("paulinaMock21", "mail", "mock.jpg", "mrsmock69"))
        add_to_db("characters", ("paulinaMock21" ,"Yanko", "Ranger", "Hunter", "Lizardfolk", "Lizardfolk", 30, 20, 20, 12, 18, 16, 12, 8, 77, "lizardboi.jpg"))
        # print(read_db("characters", "*", "WHERE user_id = 'paulinaMock21'"))
        add_to_db("characters", ("paulinaMock21" ,"Fashum", "Ranger", "Hunter", "Lizardfolk", "Lizardfolk", 30, 20, 20, 12, 18, 16, 12, 8, 77, "lizardboi.jpg"))
        
        yield client_2
    
    delete_from_db("active_room", "WHERE user_id = 'paulinaMock21'")
    delete_from_db("users", "WHERE user_id = 'paulinaMock21'")
    delete_from_db("room_object", "WHERE user_id = 'paulinaMock21'")
    delete_from_db("characters", "WHERE user_id = 'paulinaMock21'")





# Testing client without authenticated user
@pytest.fixture
def client_3():
    app.config['TESTING'] = True
    app.test_client_class = FlaskClient
    add_to_db("users", ("6969testingCharnky", "treach01@luther.edu", "mock.jpg", "Charnk98"))
    with app.test_client() as client_3:
        yield client_3
    delete_from_db("users", "WHERE username = 'Charnk98'")
    







# Testing client 
def test_invalid_user_and_new_user(client_3, mocker):

    failed_login_view = client_3.get('/home', follow_redirects=True)
    assert b'Welcome to' in failed_login_view.data
    assert b'This form allows you to spectate in the active room with the provided id.' in failed_login_view.data

    mocker.patch("flask_login.utils._get_user", return_value = User("fakeUser404", "fakeUser@mail.com", "mockUserPic.jpg", None))
    delete_from_db("users", "WHERE user_id = 'fakeUser404'")
    add_to_db("users", ("fakeUser404", "fakeUser@mail.com", "mockUserPic.jpg", None))

    set_user_name_view = client_3.get("/home", follow_redirects=True)

    assert b'Please enter in your username! It can be changed at any time in the user settings page. Please note that your username must be unique across all users.' in set_user_name_view.data

    data = {"username":"Charnk98"}
    data["csrf_token"] = client_3.csrf_token
    

    bad_user_name_attempt = client_3.post("/home", data=data, follow_redirects=True)

    assert b"Another user has that username!"  in bad_user_name_attempt.data

    data = {"username":""}
    data["csrf_token"] = client_3.csrf_token

    missing_user_name_attempt = client_3.post("/home", data=data, follow_redirects=True)

    assert b"You must enter something for your username." in missing_user_name_attempt.data
    

    data = {"username":"AnotherMocker1"}
    data["csrf_token"] = client_3.csrf_token
    mocker.patch("flask_login.utils._get_user", return_value = User("fakeUser404", "fakeUser@mail.com", "mockUserPic.jpg", "AnotherMocker1"))

    good_user_name_attmept = client_3.post("/home", data=data, follow_redirects=True)


    assert b'AnotherMocker1' in good_user_name_attmept.data
    assert b'This form allows you to (re)join and play in the active room with the provided id.' in good_user_name_attmept.data
    


def test_join_active_room(mocker, client_2, client_3):

    client_2.get("/home", follow_redirects=True)

    data = {"play_room_id":"123ABC", "csrf_token":client_2.csrf_token}

    test_join_fake_room = client_2.post("/home", data= data, follow_redirects=True)
    
    assert b"There is not an open room with that key!" in test_join_fake_room.data

    data = {"spectate_room_id":"123ABC", "csrf_token":client_2.csrf_token}

    test_spectate_fake_room =  client_2.post("/home", data= data, follow_redirects=True)

    assert b'There is not an open room with that key!' in test_spectate_fake_room.data

    data = {"play_room_id":"ABC123", "csrf_token":client_2.csrf_token}

    test_join_active_room = client_2.post("/home", data=data, follow_redirects=True)

    assert b'Add a Character First' in test_join_active_room.data

    client_2.get("/home", follow_redirects=True)

    data1 = {"spectate_room_id":"ABC123", "csrf_token":client_2.csrf_token}
    
    authentic_user_spectate = client_2.post("/home", data=data1, follow_redirects=True)
    
    assert b'Initiative Order' in authentic_user_spectate.data
    
    data2 = {"spectate_room_id":"ABC123", "csrf_token":client_3.csrf_token}
    
    client_3.get("/home", follow_redirects=True)

    unauthenticated_user_spectate = client_3.post("/home", data=data2, follow_redirects=True)

    assert b'Initiative Order' in unauthenticated_user_spectate.data

    mocker.patch("flask_login.utils._get_user", return_value = User("fakeUser404", "fakeUser@mail.com", "mockUserPic.jpg", "AnotherMocker1"))

    client_3.get("/home", follow_redirects=True)

    data = {"play_room_id":"ABC123", "csrf_token":client_3.csrf_token, }

    no_characters_connect = client_3.post("/home", data=data,follow_redirects=True )

    assert b"Add a Character" in no_characters_connect.data
    





# Testing Authenticated User Login
# Client  accesses the application with an authenticated user and thus is logged in
# This test ensures that the pages accessed by a basic user just entering the site without any 
# input data other than their user name 
def test_login(client_1):

    home_view = client_1.get('/home', follow_redirects=True)
    characters_view = client_1.get('/characters')
    settings_view = client_1.get('/user/settings')

    assert b'This form allows you to (re)join and play in the active room with the provided id.' in home_view.data
    assert b'Create a Character' in characters_view.data
    assert b'Account Actions' in settings_view.data









# Testing character and room creation
# Utilizing our fake( but authenticated !)user, we check to make sure character creation works as expected
# ex. throws correct errors, redirects to the proper pages 
@pytest.mark.parametrize("fields, inputs, expected", get_cases("character_creation"))
def test_character_create(client_2, fields, inputs, expected):
    # This line sets up the app context... Don't ask me why it is needed...
    char_create_view = client_2.get("/characters/create")

    valid_inputs = []
    for items in inputs:
        try:
            valid_inputs.append(int(items))
        except:
            valid_inputs.append(items)

    data = {fields[x]:valid_inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_2.csrf_token
    
    character_create_attempt = client_2.post("/characters/create", data = data, follow_redirects=True)
    assert bytes(expected,'utf-8') in character_create_attempt.data









# Testing creation of rooms 
# Utilize client 1(User w/o data)
@pytest.mark.parametrize("fields, inputs, expected", get_cases("room_creation"))
def test_room_create(client_1, fields, inputs, expected):
    rooms_view = client_1.get("/rooms/create")

    data = {fields[x]:inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_1.csrf_token

    create_room_attempt = client_1.post("/rooms/create", data = data, follow_redirects= True)

    assert bytes(expected, 'utf-8') in create_room_attempt.data







@pytest.mark.parametrize("fields, inputs, expected", get_cases("room_edit"))
def test_room_edit(client_2, fields, inputs, expected):
    
    room_row_number = read_db("room_object","row_id", "WHERE user_id = 'paulinaMock21' and room_name = 'Dungeon Battle'")[0][0]
    room_view = client_2.get(f"/rooms/{room_row_number}")

    data = {fields[x]:inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_2.csrf_token

    room_edit_test = client_2.post(f"/rooms/{room_row_number}", data=data, follow_redirects=True)

    assert bytes(expected, 'utf-8') in room_edit_test.data








# Test changing a user's sitename
# Only checks that illegal characters fail 
# Utilize Client 1 (User w/o data)
# Note: Checking for user name change success will fail due to means with which we authenticate fake users
@pytest.mark.parametrize("fields, inputs, expected", get_cases("username"))
def test_username_change(client_1, fields, inputs, expected, mocker):
    settings_view = client_1.get("/user/settings")

    data = {fields[0]:inputs[0]}
    data["csrf_token"] = client_1.csrf_token

    try:
        if fields[1]:
            mocker.patch("flask_login.utils._get_user", return_value = User("mocksterid", "mail", "mock.jpg", f"{inputs[0]}"))
    except:
        pass

    update_username_attempt = client_1.post("/user/settings", data = data, follow_redirects= True)
    

    assert bytes(expected, 'utf-8') in update_username_attempt.data







# Testing editing a character
# utilize Client_2 - > User with data 
@pytest.mark.parametrize("fields, inputs, expected", get_cases("edit_char"))
def test_edit_character(client_2, inputs, fields, expected):

    character_edit_view = client_2.get(f"/characters/edit/{inputs[14]}")
    print(character_edit_view.data)
    if b'Error Code' not in character_edit_view.data:
        valid_inputs = []
        for items in inputs:
            try:
                valid_inputs.append(int(items))
            except:
                valid_inputs.append(items)
        data = {fields[x]:inputs[x] for x in range(len(fields))}
        data["csrf_token"] = client_2.csrf_token
        edit_char = client_2.post(f"/characters/edit/{inputs[14]}", data=data, follow_redirects=True)

        assert bytes(expected, 'utf-8') in edit_char.data
    else:
        assert bytes(expected, 'utf-8') in character_edit_view.data




# Testing deletion of characters
# utilize Client_2 - > User with data 
def test_delete_character(client_2):
    characters_view = client_2.get("/characters")

    data = {"character_name":"Yanko", "csrf_token":client_2.csrf_token}
    del_char = client_2.post("/characters", data=data, follow_redirects=True )

    assert b'Yanko' not in del_char.data




def test_logout_user(client_2, mocker):
    logged_out = client_2.get("/logout", follow_redirects=True)
    mocker.patch("flask_login.utils._get_user", return_value = AnonymousUser())
    login_attempt = client_2.get("/home", follow_redirects=True)

    assert b"""Welcome to Wizards of the Driftless (formerly Wizards of the Plains) Online Battle Simulator! You currently are not logged in. As such, you cannot access most of the site's functionality. If you wish to do anything other than spectate a room, please log in!""" in login_attempt.data





# Check user info wipe route
# NOTE: this test simply checks DB correctness post-wipe and
# then does a mock wipe of user from flask login's user context 

def test_delete_user(client_2, mocker):
    del_user = client_2.get("/delete")

    mocker.patch("flask_login.utils._get_user", return_value = AnonymousUser())

    log_lis = read_db("log", "user_id", f"WHERE user_id = 'paulinaMock21'")
    chat_lis = read_db("chat", "user_id", f"WHERE user_id = 'paulinaMock21'")
    active_rooms_lis = read_db("active_room", "user_id", f"WHERE user_id = 'paulinaMock21'")
    room_object_lis = read_db("room_object", "user_id", f"WHERE user_id = 'paulinaMock21'")
    user_lis = read_db("users", "user_id", f"WHERE user_id = 'paulinaMock21'")
    characters_list = read_db("characters", "user_id", f"WHERE user_id = 'paulinaMock21'")
    assert not log_lis
    assert not chat_lis
    assert not active_rooms_lis
    assert not room_object_lis
    assert not user_lis
    assert not characters_list
    

    home_screen_check = client_2.get("/home")
    assert b"""Welcome to Wizards of the Driftless (formerly Wizards of the Plains) Online Battle Simulator! You currently are not logged in. As such, you cannot access most of the site's functionality. If you wish to do anything other than spectate a room, please log in!""" in home_screen_check.data




@pytest.mark.parametrize("inputs, expected", get_cases("check_spam"))
def test_user_spamming(client_2, inputs, expected):
    fake_time_used = "2021-03-28 16:48:30"

    chats = inputs
    is_spam = determine_if_user_spamming(chats, fake_time_used)

    assert expected == is_spam




# @pytest.mark.parametrize("inputs, expected", get_cases("add_icon"))
# def test_add_data(client_2, inputs, expected):




# SocketIO Event Tests

# gotta be a better way to do this
def test_client_connect(client_2):
    app.config["FLASK_DEBUG"] = 0
    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
    
    with app.app_context():
        socketio_client = socketio.test_client(app, namespace="/combat")

        row_id = read_db("room_object", "row_id", "WHERE room_name = 'Dungeon Battle'")[0][0]
        app_context = client_2.get(f"/room/{row_id}")
        open_room_test = client_2.post("/generate_room", data={"room_id":f"{row_id}", "csrf_token":client_2.csrf_token}, follow_redirects=True)

        assert socketio_client.is_connected("/combat")
        assert not socketio_client.is_connected("/")

        room_id = read_db("room_object", "active_room_id", f"WHERE row_id = '{row_id}'")[0][0]

        # Was originally needed
        # with app.test_request_context():

        # get the client's sid
        socketio_client.emit("get_sid", {}, namespace="/combat")
        response = socketio_client.get_received(namespace="/combat")

        socketio_id = response[0]['args'][0]['id']

        # have the client join the room
        socketio_client.emit("on_join", {'room_id': room_id}, namespace="/combat")
        response = socketio_client.get_received(namespace="/combat")

        # Ensure the right event was sent back
        assert len(response) == 1
        assert response[0]['name'] == 'joined'
        
        # Get the client's rooms
        room_ids = rooms(socketio_id, namespace="/combat")

        # Ensure that the rooms the client is in are correct
        assert socketio_id == room_ids[0]
        assert room_id == room_ids[1]

        socketio_client.emit("join_actions", {'room_id': room_id}, namespace="/combat")
        response = socketio_client.get_received(namespace="/combat")

        # Ensure the basic 3 responses are sent
        print(response)
        assert len(response) == 3
        assert response[0]['args'][0]['desc'] == 'mrsmock69 Connected'
        assert response[1]['args'][0]['desc'] == 'Initiative List Received'
        assert response[2]['args'][0]['desc'] == 'Chat History Received'