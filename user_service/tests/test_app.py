from flask_bcrypt import Bcrypt
import jwt
from config import TestingConfig
import pytest
import sys
import os
import logging
from u_services import db, create_app
from u_services.models import User
from werkzeug.security import generate_password_hash
from unittest.mock import patch
import datetime
import pytz
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)


bcrypt = Bcrypt()
@pytest.fixture(scope='module')
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def clear_db():
    """Clears the database before each test."""
    yield
    db.session.remove()
    db.drop_all()
    db.create_all()


def test_register_missing_data(client):
    response = client.post('/api/register', json={})
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Missing data'}


def test_register_invalid_email_format(client):
    response = client.post('/api/register', json={
        'username': 'testuser',
        'password': 'password123',
        'email': 'invalid-email'
    })
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid email format'}


def test_register_short_password(client):
    response = client.post('/api/register', json={
        'username': 'testuser',
        'password': 'short',
        'email': 'test@example.com'
    })
    assert response.status_code == 400
    assert response.get_json() == {
        'message': 'Password must be at least 8 characters long'}


def test_register_user_already_exists(client):
    user = User(username='existinguser',
                email='existing@example.com', password='password123')
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/register', json={
        'username': 'newuser',
        'password': 'password123',
        'email': 'existing@example.com'
    })
    assert response.status_code == 409
    assert response.get_json() == {
        'message': 'User with this email already exists'}


def test_register_success(client):
    response = client.post('/api/register', json={
        'username': 'newuser',
        'password': 'password123',
        'email': 'new@example.com'
    })
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Registered successfully'}

    # Verify user was added to the database
    user = User.query.filter_by(email='new@example.com').first()
    assert user is not None
    assert user.username == 'newuser'


def test_login_missing_data(client):
    response = client.post('/api/login', json={})
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Missing username or password'}


def test_login_invalid_credentials(client):
    user = User(username='testuser', email='test@example.com',
                password=bcrypt.generate_password_hash('password123').decode('utf-8'))
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Invalid credentials'}


def test_login_user_not_found(client):
    response = client.post('/api/login', json={
        'username': 'nonexistentuser',
        'password': 'password123'
    })
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Invalid credentials'}

@patch('u_services.view.jwt.encode')
@patch('u_services.view.datetime')
def test_login_successful(mock_datetime, mock_jwt_encode):
    local_tz = datetime.timezone(datetime.timedelta(hours=0))
    now = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=local_tz)
    utc_now = now.astimezone(pytz.utc)
    exp_time = utc_now + datetime.timedelta(hours=1)
    mock_datetime.datetime.now.return_value = now
    mock_datetime.datetime.astimezone.return_value = utc_now
    mock_jwt_encode.return_value = 'mocked_token'

    user = User(id=1, username='testuser',password= 'password123', email="example@abc.com")
    db.session.add(user)
    db.session.commit()

    token = jwt.encode({
        'user_id': user.id,
        'iat': now,
        'exp': exp_time
    }, 'secret_key', algorithm='HS256')

    assert token == 'mocked_token'



def test_login_token_generation_failure(client, monkeypatch):
    password = bcrypt.generate_password_hash('password123').decode('utf-8')
    user = User(username='testuser',
                email='test@example.com', password=password)
    db.session.add(user)
    db.session.commit()

    def mock_jwt_encode(*args, **kwargs):
        raise Exception("Token generation failed")

    monkeypatch.setattr(jwt, 'encode', mock_jwt_encode)

    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 500
    assert response.get_json() == {'message': 'Token generation failed'}
