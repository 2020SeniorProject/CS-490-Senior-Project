import os, sys
import tempfile
import pytest

# https://flask.palletsprojects.com/en/1.1.x/testing/

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app, socketio
from db import create_dbs

# pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning:/.*\w+\.?\w+ module ")

# 
#  TO AVOID DEPRECATION WARNING FROM OUR 3rd PARTY LIBRARIES 
#  I RECOMMEND USING THE COMMAND 
#  pytest path-to-test-folder -W ignore::DeprecationWarning
#  As
# 


@pytest.fixture
def client_1():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

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




def test_empty_db(client_1):
    """Start with a blank database."""

    rv = client_1.get('/')
    assert b'Welcome to' in rv.data

def login(client_1)

    rv = client_1.get('/login',  ,follow_redirects=True)








