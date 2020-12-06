import os, sys
import tempfile
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app

@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        with app.app.app_context():
            app.create_dbs()
        yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE'])



