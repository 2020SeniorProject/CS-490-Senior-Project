# third parties
import pytest
# from flask_login import LoginManager, UserMixin

# python library imports
import os, sys
import tempfile
from unittest import mock


# https://flask.palletsprojects.com/en/1.1.x/testing/
# Internal imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app, socketio, current_user
from db import create_dbs

# pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning:/.*\w+\.?\w+ module ")

# 
#  TO AVOID DEPRECATION WARNING FROM OUR 3rd PARTY LIBRARIES 
#  I RECOMMEND USING THE COMMAND 
#  python3 -m pytest tests/test_app.py -W ignore::DeprecationWarning
#  
# 
    

@pytest.fixture
def client_1(monkeypatch):
    # monkeypatch.setenv("")
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    # monkeypatch.setenv("GOOGLE_CLIENT_ID", "211539095216-3dnbifedm4u5599jf7spaomla4thoju6")
    # monkeypatch.setenv("GOOGLE_CLIEND_SECRET", "mDU7FgZe3vN5gehLntr5SESD")



    with app.test_client() as client_1:
        
        with app.app_context():
            create_dbs()
        yield client_1

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
def client_2():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client_1:
        with app.app_context():
            
            create_dbs()
        yield client_2

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
@mock.patch("flask_login.utils._get_user")
def mock_authenticated_user(monkeypatch):
    user = mock.MagicMock()
    user.is_authenticated = True
    user.user_id = lambda self: "6969Goober"
    user.site_name = lambda self: "Big_goober"
    current_user.return_value = user





# TODO: Figure out how tests can log in through google API
def test_invalid_user(client_1):

    rv = client_1.get('/home', follow_redirects=True)
    assert b'Welcome to' in rv.data


@mock.patch("flask_login.utils._get_user")
def test_login(*args, **keywargs):
    pass_obj = args
    user = mock.MagicMock()
    # user.is_authenticated = True
    user.name = "Mr Mock"
    current_user.return_value.get_user_id = "1234"
    current_user.return_value.get_site_name = "MrMOCKS"
    current_user.return_value = user

    client = app.test_client()

    rv = client.get("/", follow_redirects=True)
    assert b'Create room' in rv.data







