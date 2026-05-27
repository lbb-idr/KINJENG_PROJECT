import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import create_app
from app.utils.database import DatabaseManager

@pytest.fixture(autouse=True)
def test_db():
    """Use in-memory SQLite for all tests"""
    import tempfile
    db_path = os.path.join(tempfile.gettempdir(), 'kinjeng_test.db')
    os.environ['SQLITE_PATH'] = db_path
    db = DatabaseManager()
    db._initialized = False
    db.init_app()
    yield
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ.pop('SQLITE_PATH', None)

@pytest.fixture
def app():
    os.environ['FLASK_DEBUG'] = 'False'
    application = create_app()
    application.config['TESTING'] = True
    return application

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
