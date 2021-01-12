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
import os, sys
import tempfile
from unittest import mock


# https://flask.palletsprojects.com/en/1.1.x/testing/
# Internal imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app, socketio
from db import create_dbs, add_to_db, delete_from_db
import wtforms.csrf 
from classes import User


# 
#  TO AVOID DEPRECATION WARNING FROM OUR 3rd PARTY LIBRARIES 
#  I RECOMMEND USING THE COMMAND 
#  python3 -m pytest tests/test_app.py -W ignore::DeprecationWarning
#  

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
def test_login(client_1):

    home_view = client_1.get('/home', follow_redirects=True)
    characters_view = client_1.get('/characters')

    assert b'Create a room' in home_view.data
    assert b'Create a Character' in characters_view.data


def test_character_create(client_1):
    char_create_view = client_1.get("/characters/create")
    # signed_token = request.form['csrf_token']
    # print(char_create_view.data)
    # print(signed_token)
    data = {"name":"Yanko", "race":"Lizardfolk", "subrace":"Lizardfolk", "speed":20, "classname":"Ranger", 
    "subclass":"Hunter", "level":20, "strength":12, "dexterity":18, "constitution":16, "intelligence":12, 
    "wisdom":18, "charisma":8, "hitpoints": 77, "char_token":"lizardboi.jpg", "csrf_token":client_1.csrf_token}
    char_create = client_1.post("/characters/create", data=data, follow_redirects = True)
    
    assert b'Yanko' in char_create.data


