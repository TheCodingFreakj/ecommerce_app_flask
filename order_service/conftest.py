# tests/conftest.py
import pytest
from . import app, db  # Adjust the import based on your app structure

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

    # Teardown
    with app.app_context():
        db.drop_all()
