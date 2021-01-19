# third parties
import pytest
import flask_login 
import flask
from flask import Flask, session
from flask.testing import FlaskClient as BaseFlaskClient
from flask_login import current_user, UserMixin
from flask_wtf.csrf import generate_csrf
from flask_socketio import SocketIO, emit, join_room, close_room
from requests import get, post, request

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
from db import create_dbs, add_to_db, delete_from_db, read_db
import wtforms.csrf 
from classes import User


# 
#  TO AVOID DEPRECATION WARNING FROM OUR 3rd PARTY LIBRARIES 
#  I RECOMMEND USING THE COMMAND 
#  python3 -m pytest tests/test_app.py -W ignore::DeprecationWarning
#  


def get_cases(category: str):
    with open(pathlib.Path(__file__).with_suffix(".toml")) as f:
        all_cases = toml.load(f)
        for case in all_cases[category]:
            yield (case.get("fields"), case.get("inputs"), case.get("expected"))



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





# Testing client with authenticated user 
# but nothing else in the db except another User named Charnk(for site name test)
@pytest.fixture
def client_1(mocker):
    app.config['TESTING'] = True
    app.test_client_class = FlaskClient
    add_to_db("users", ("6969testingCharnky", "Charles", "treach01@luther.edu", "mock.jpg", "Charnk98"))
    with app.test_client() as client_1:
        create_dbs()
        mocker.patch("flask_login.utils._get_user", return_value = User("mocksterid", "john Mock", "mail", "mock.jpg", "mrMock420"))
        add_to_db("users", ("mocksterid", "john Mock", "mail", "mock.jpg", "mrMock420"))
        yield client_1
    
    delete_from_db("users", "WHERE site_name = 'Charnk98'")
    delete_from_db("users", "WHERE user_id = 'mocksterid'")
    delete_from_db("room_object", "WHERE user_key = 'mocksterid'")
    delete_from_db("characters", "WHERE user_key = 'mocksterid'")

#User with a character in the DB and 
# a room in it for socketio testing
@pytest.fixture
def client_2(mocker):
    app.config['TESTING'] = True
    app.test_client_class = FlaskClient
    with app.test_client() as client_2:
        create_dbs()
        mocker.patch("flask_login.utils._get_user", return_value = User("paulinaMock21", "Paulina Mock", "mail", "mock.jpg", "mrsmock69"))
        add_to_db("room_object", ("paulinaMock21", "Dungeon Battle", "", "", "this_is_sweet_map.jpg", "This is going to be an intense batle"))
        add_to_db("users", ("paulinaMock21", "Paulina Mock", "mail", "mock.jpg", "mrsmock69"))
        add_to_db("characters", ["paulinaMock21" ,"Yanko", "Lizardfolk", "Lizardfolk", 20, "Ranger", "Hunter", 20, 12, 18, 16, 12, 18, 8, 77, "lizardboi.jpg"])
        yield client_2
    
    delete_from_db("users", "WHERE user_id = 'paulinaMock21'")
    delete_from_db("room_object", "WHERE user_key = 'paulinaMock21'")
    delete_from_db("characters", "WHERE user_key = 'paulinaMock21'")




# Testing client without authenticated user
@pytest.fixture
def client_3():
    app.config['TESTING'] = True
    with app.test_client() as client_3:
        yield client_3


@pytest.fixture
def socket_client(client_2):
    yield socket_client




# Testing client 
def test_invalid_user(client_3):

    login_view = client_3.get('/home', follow_redirects=True)
    assert b'Welcome to' in login_view.data


# Testing Authenticated User Login
# Client  accesses the application with an authenticated user and thus is logged in
# This test ensures that the pages accessed by a basic user just entering the site without any 
# input data other than their user name 
def test_login(client_1):

    home_view = client_1.get('/home', follow_redirects=True)
    characters_view = client_1.get('/characters')
    settings_view = client_1.get('/user/settings')
    play_entry_view = client_1.get("/play")

    assert b'Create a room' in home_view.data
    assert b'Create a Character' in characters_view.data
    assert b'Update your username:' in settings_view.data
    assert b'Enter an 8 character room id' in play_entry_view.data



# Testing character and room creation
# Utilizing our fake( but authenticated !)user, we check to make sure character creation works as expected
# ex. throws correct errors, redirects to the proper pages 
@pytest.mark.parametrize("fields, inputs, expected", get_cases("character_creation"))
def test_character_create(client_1, fields, inputs, expected):
    # This line sets up the app context... Don't ask me why it is needed...
    char_create_view = client_1.get("/characters/create")

    valid_inputs = []
    for items in inputs:
        try:
            valid_inputs.append(int(items))
        except:
            valid_inputs.append(items)

    data = {fields[x]:valid_inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_1.csrf_token

    character_create_attempt = client_1.post("/characters/create", data = data, follow_redirects=True)
    assert bytes(expected,'utf-8') in character_create_attempt.data

# Testing creation of rooms 
# Utilize client 1(User w/o data)
@pytest.mark.parametrize("fields, inputs, expected", get_cases("room_creation"))
def test_room_create(client_1, fields, inputs, expected):
    rooms_view = client_1.get("/room/create")

    data = {fields[x]:inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_1.csrf_token

    create_room_attempt = client_1.post("/room/create", data = data, follow_redirects= True)

    assert bytes(expected, 'utf-8') in create_room_attempt.data


@pytest.mark.parametrize("fields, inputs, expected", get_cases("room_edit"))
def test_room_edit(client_2, fields, inputs, expected):
    
    room_row_number = read_db("room_object","row_id", "WHERE user_key = 'paulinaMock21' and room_name = 'Dungeon Battle'")[0][0]
    room_view = client_2.get(f"/room/{room_row_number}")

    data = {fields[x]:inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_2.csrf_token

    room_edit_test = client_2.post(f"/room/{room_row_number}", data=data, follow_redirects=True)

    assert bytes(expected, 'utf-8') in room_edit_test.data



# Test changing a user's sitename
# Only checks that illegal characters fail 
# Utilize Client 1 (User w/o data)
# Note: Checking for user name change success will fail due to means with which we authenticate fake users
@pytest.mark.parametrize("fields, inputs, expected", get_cases("site_name"))
def test_site_name_change(client_1, fields, inputs, expected):
    settings_view = client_1.get("/user/settings")

    data = {fields[0]:inputs[0]}
    data["csrf_token"] = client_1.csrf_token

    update_site_name_attempt = client_1.post("/user/settings", data = data, follow_redirects= True)
    assert bytes(expected, 'utf-8') in update_site_name_attempt.data

# Testing editing a character
# utilize Client_2 - > User with data 
@pytest.mark.parametrize("fields, inputs, expected", get_cases("edit_char"))
def test_edit_character(client_2, inputs, fields, expected):

    character_edit_view = client_2.get(f"/characters/edit/{inputs[14]}")
    
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

# Testing deletion of characters
# utilize Client_2 - > User with data 
def test_delete_character(client_2):
    characters_view = client_2.get("/characters")

    data = {"character_name":"Yanko", "csrf_token":client_2.csrf_token}
    del_char = client_2.post("/characters", data=data, follow_redirects=True )

    assert b'Yanko' not in del_char.data

# SocketIO Event Tests

# def test_open_room(client_2):
#     room_id = read_db("room_object", "row_id", "WHERE room_name = 'Dungeon Battle'")[0][0]

#     app_context = client_2.get(f"/room/{room_id}")
#     open_room_test = client_2.post("/generate_room", data={"room_name":"Dungeon Battle", "csrf_token":client_2.csrf_token}, follow_redirects=True)
    
#     socket_client = socketio.test_client(app, flask_test_client=client_2)
#     socket_client.connect("/combat")
    

#     data_recv = socket_client.get_received()

#     print(data_recv)

    # assert b'Yanko' in open_room_test.data


def testing_add_characters(socket_client, client_2):
    room_object_id = read_db("room_object", "row_id", "WHERE room_name = 'Dungeon Battle' and user_key= 'paulinaMock21'")[0][0]
    app_context = client_2.get(f"/room/{room_object_id}")
    open_room_test = client_2.post("/generate_room", data={"room_name":"Dungeon Battle", "csrf_token":client_2.csrf_token}, follow_redirects=True)

    room_id = read_db("room_object", "active_room_id", f"WHERE row_id= {room_object_id}")

    socket_client = socketio.test_client(app, namespace="/combat", flask_test_client=client_2)
    socket_client.join_room(room_id)
    # socket_client.emit("join_actions", {"room_id":room_id, "character_name":""}, room_id=room_id)
    socket_join_events = socket_client.get_received()
    # print(socket_join_events)
    assert socket_join_events[0]["site_name"] == mrsmock69

    # add_char_event = socket_client.emit("add_character", {"character_name":"Yanko", "site_name":"mrsmock69", "room_id":room_id})



