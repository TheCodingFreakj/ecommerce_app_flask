from unittest.mock import patch, AsyncMock
from functools import wraps
from o_services.view import order_bp
from config import TestingConfig
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient
from flask import Flask, jsonify, request
from o_services.models import Order
import pytest
from o_services import db, create_app
import sys
import os
import logging
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# Set up logging for debugging
logging.basicConfig(level=logging.CRITICAL)


@pytest.fixture(scope='session', autouse=True)
def configure_logging():
    logging.getLogger('o_services').setLevel(logging.CRITICAL)


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


@pytest.fixture
def create_order():
    order = Order(customer_name='testuser',
                  customer_email='testemail',
                  total_price=1)
    db.session.add(order)
    db.session.commit()

    return order


def mock_validate_token(valid, user_id=None, username=None):
    def _mock_validate_token(f):
        def wrapper(*args, **kwargs):
            authorizered_user = {
                "user_id": 1, "username": 'testuser'
            }
            if valid and user_id == authorizered_user["user_id"]:
                validation_response = {'user_id': user_id, 'username': username}
                return f(validation_response)
            else:
                return jsonify({'error': 'You are not allowed to view this order'}), 403
        return wrapper
    return _mock_validate_token


def test_missing_token(client, create_order):
    order = create_order
    response = client.post(f'/api/view-your-orders/{order.id}')
    assert response.status_code == 403
    assert response.get_json() == {'error': 'Unauthorized access'}


@patch('o_services.view.token_required', mock_validate_token(False))
def test_invalid_token(client, create_order):
    order = create_order
    response = client.post(f'/api/view-your-orders/{order.id}')
    assert response.status_code == 403
    assert response.get_json() == {'error': 'Unauthorized access'}


@patch('o_services.view.token_required', mock_validate_token(True, user_id=2, username='testuser2'))
def test_order_not_found(client, create_order):
    order = create_order
    response = client.post(f'/api/view-your-orders/{order.id}')
    assert response.status_code == 403


@patch('o_services.view.token_required', mock_validate_token(True, user_id=2, username='testuser2'))
def test_user_not_authorized(client, create_order):
    order = create_order
    response = client.post(f'/api/view-your-orders/{order.id}')
    assert response.status_code == 403
   



