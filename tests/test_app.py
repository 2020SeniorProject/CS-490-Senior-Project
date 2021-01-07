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
#


@pytest.fixture
def client_1(mocker):

    app.config['TESTING'] = True
    with app.test_client() as client_1:
        mocker.patch("flask_login.utils._get_user", return_value = User("mocksterid", "john Mock", "mail", "mock.jpg", "mrMock420"))
        yield client_1



@pytest.fixture
def client_2():
    app.config['TESTING'] = True
    with app.test_client() as client_2:
        yield client_2



def test_invalid_user(client_2):

    login_view = client_2.get('/home', follow_redirects=True)
    assert b'Welcome to' in login_view.data



def test_login(client_1):

    home_view = client_1.get('/home', follow_redirects=True)
    chracters_view = client_1.get('/characters')

    assert b'Create a room' in home_view.data
    assert b'Character Name' in characters_view.data











