from p_services.view import product_bp
from config import TestingConfig
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient
from flask import Flask, jsonify, request
from p_services.models import Product
from p_services import db, create_app
import pytest
import asyncio
import sys
import os
import logging
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


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


@patch('p_services.view.token_required', mock_validate_token(True, user_id=1, username='testuser'))
def test_update_product_not_found(client, mocker):

    product = Product(name="Product 121",
                      description="Description for Product 132",
                      price=132.00,
                      stock=13200,last_modified_by="testuser")
    db.session.add(product)
    db.session.commit()
    product_data = {
        "name": "Updated Product",
        "description": "Updated description",
        "price": 100.00,
        "stock": 10,
        "version": 1,
        "last_modified_by":"testuser"
    }

    # Call the product endpoint
    response = client.put(
        '/products/12', json=product_data)
    logging.debug(f"Response received: {response.status_code}")

    # Validate the response
    assert response.status_code == 404
    

@patch('p_services.view.token_required', mock_validate_token(True, user_id=1, username='testuser'))
def test_update_product_conflict(client, mocker):

    # Define the product data
    product_data = {
        "name": "Updated Product22",
        "description": "Updated description",
        "price": 100.00,
        "stock": 10,
        "version": 1  ,# Old version, should cause conflict
        "last_modified_by":"testuser"
    }

    # Call the product endpoint
    response = client.put(
        '/api/products/1', json=product_data)
    logging.debug(f"Response received: {response.status_code}")

    # Validate the response
    assert response.status_code == 403
