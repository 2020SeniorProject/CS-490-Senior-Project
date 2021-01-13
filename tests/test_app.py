# third parties
import pytest
import flask_login 
import flask
from flask import Flask, session
from flask.testing import FlaskClient as BaseFlaskClient
from flask_login import current_user, UserMixin
from flask_wtf.csrf import generate_csrf
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
@pytest.fixture
def client_1(mocker):
    app.config['TESTING'] = True
    app.test_client_class = FlaskClient
    with app.test_client() as client_1:
        create_dbs()
        mocker.patch("flask_login.utils._get_user", return_value = User("mocksterid", "john Mock", "mail", "mock.jpg", "mrMock420"))
        add_to_db("users", ("mocksterid", "john Mock", "mail", "mock.jpg", "mrMock420"))
        yield client_1
    
    delete_from_db("users", "WHERE user_id = 'mocksterid'")
    delete_from_db("room_object", "WHERE user_key = 'mocksterid'")
    delete_from_db("characters", "WHERE user_key = 'mocksterid'")


# Testing client without authenticated user
@pytest.fixture
def client_2():
    app.config['TESTING'] = True
    with app.test_client() as client_2:
        yield client_2


# Testing client 
def test_invalid_user(client_2):

    login_view = client_2.get('/home', follow_redirects=True)
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


@pytest.mark.parametrize("fields, inputs, expected", get_cases("room_creation"))
def test_room_create(client_1, fields, inputs, expected):
    rooms_view = client_1.get("/room/create")

    data = {fields[x]:inputs[x] for x in range(len(fields))}
    data["csrf_token"] = client_1.csrf_token

    create_room_attempt = client_1.post("/room/create", data = data, follow_redirects= True)

    assert bytes(expected, 'utf-8') in create_room_attempt.data








