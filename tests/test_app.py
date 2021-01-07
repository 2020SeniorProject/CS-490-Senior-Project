# third parties
import pytest
import flask_login 
from flask_login import current_user, UserMixin

# python library imports
import os, sys
import tempfile
from unittest import mock


# https://flask.palletsprojects.com/en/1.1.x/testing/
# Internal imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app, socketio
from db import create_dbs
from classes import User


# 
#  TO AVOID DEPRECATION WARNING FROM OUR 3rd PARTY LIBRARIES 
#  I RECOMMEND USING THE COMMAND 
#  python3 -m pytest tests/test_app.py -W ignore::DeprecationWarning
#  


# Testing client with authenticated user 
@pytest.fixture
def client_1(mocker):
    app.config['TESTING'] = True

    with app.test_client() as client_1:
        mocker.patch("flask_login.utils._get_user", return_value = User("mocksterid", "john Mock", "mail", "mock.jpg", "mrMock420"))
        # mocketr.patch("create_dbs")
        yield client_1


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
    assert b'Character Name' in characters_view.data


# def test_character_create(client_1):
#     client_1.post("/characters/create", data={"name":"Yanko", "race":"Lizardfolk", "subrace":"Lizardfolk", "speed":20, "classname":"Ranger", "subclass":"Hunter", "level":20, "strength":12, "dexterity":18, "constitution":16, "intelligence":12, "wisdom":18, "charisma":8, "hitpoints": 77, "char_token":"lizardboi.jpg"})
#     characters_view = client_1.get('/characters')
#     assert b'Yanko' in characters_view.data







