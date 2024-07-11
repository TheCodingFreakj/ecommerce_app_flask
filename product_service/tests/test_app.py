from p_services.view import product_bp
from config import TestingConfig
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient
from flask import Flask, jsonify, request
from p_services.models import Product
import pytest
import asyncio
import sys
import os
import logging
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Mock async function


async def mock_validate_token(token):
    await asyncio.sleep(0.1)  # Simulate async I/O operation
    logging.debug(f"Validating token: {token}")
    if token == "Bearer valid-token":
        return {"user_id": 1}
    return {}


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    app.register_blueprint(product_bp)
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

# Patching the validate_token function in the correct path


@patch('p_services.view.validate_token', side_effect=mock_validate_token)
def test_create_product(mock_validate_token, client, mocker):
    # Mocking the token validation response
    mock_validate_token.return_value = {"user_id": 1}
    logging.debug("Patched validate_token")

    # Define the headers with the token
    headers = {
        'Authorization': 'Bearer valid-token'
    }

    # Mocking the database session and Product model
    mock_product = mocker.MagicMock()
    mocker.patch('p_services.view.db.session.add', return_value=None)
    mocker.patch('p_services.view.db.session.commit', return_value=None)
    mocker.patch('p_services.models.Product', return_value=mock_product)
    logging.debug("Patched database session and Product model")

    # Define the product data
    product_data = {'description': 'A test product',
                    'name': 'Test Product',
                    'price': 99.99,
                    'stock': 10}

    # Call the product endpoint
    response = client.post('/products', json=product_data, headers=headers)
    logging.debug(f"Response received: {response.status_code}")

    # Validate the response
    assert response.status_code == 201
    assert response.json['name'] == 'Test Product'
    assert response.json['description'] == 'A test product'
    assert response.json['price'] == 99.99
    assert response.json['stock'] == 10

 


def test_create_product_token_missing(client):
    logging.debug("Testing with missing token")

    # Define the headers without the token
    headers = {}

    # Define the product data
    product_data = {
        "name": "Test Product",
        "description": "A test product",
        "price": 99.99,
        "stock": 10
    }

    # Call the product endpoint
    response =  client.post('/products', json=product_data, headers=headers)
    logging.debug(f"Response received: {response.status_code}")

    # Validate the response
    assert response.status_code == 403
    assert response.json['error'] == 'Unauthorized access'


# Helper function to create a mock Product object
def create_mock_product():
    mock_product = MagicMock(spec=Product)
    mock_product.id = 1
    mock_product.name = "Old Product"
    mock_product.description = "Old description"
    mock_product.price = 50.00
    mock_product.stock = 5
    mock_product.version = 1
    mock_product.last_modified_by = 1
    mock_product.to_dict.return_value = {
        'id': mock_product.id,
        'name': mock_product.name,
        'description': mock_product.description,
        'price': mock_product.price,
        'stock': mock_product.stock,
        'version': mock_product.version,
        'last_modified_by': mock_product.last_modified_by
    }
    return mock_product

# Patching the validate_token function in the correct path within the test cases

def test_update_product_success(client, mocker):
    # Mock the validate_token function
    with patch('p_services.view.validate_token', side_effect=mock_validate_token):
        # Mocking the token validation response
        logging.debug("Patched validate_token")

        # Define the headers with the token
        headers = {
            'Authorization': 'Bearer valid-token'
        }

        # Create a mock product
        mock_product = create_mock_product()

        # Mocking the query methods
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_product

        mocker.patch('p_services.models.Product.query', new=mock_query)
        mocker.patch('p_services.view.db.session.commit', return_value=None)
        mocker.patch('p_services.view.db.session.rollback', return_value=None)

        # Mocking lock_manager
        mock_lock = mocker.MagicMock()
        mock_lock.__enter__.return_value = None
        mock_lock.__exit__.return_value = None
        mocker.patch('p_services.view.lock_manager.acquire_lock', return_value=mock_lock)

        # Define the product data
        product_data = {
            "name": "Updated Product",
            "description": "Updated description",
            "price": 100.00,
            "stock": 10,
            "version": 1
        }

        # Call the product endpoint
        response =  client.put('/products/1', json=product_data, headers=headers)
        logging.debug(f"Response received: {response.status_code}")

        # Validate the response
        assert response.status_code == 200
        assert response.json['name'] == 'Old Product'
        assert response.json['description'] == 'Old description'
        assert response.json['price'] == 50.00
        assert response.json['stock'] == 5


def test_update_product_not_found(client, mocker):
    # Mock the validate_token function
    with patch('p_services.view.validate_token', side_effect=mock_validate_token):
        logging.debug("Testing product not found")

        # Define the headers with the token
        headers = {
            'Authorization': 'Bearer valid-token'
        }

        # Mocking the query methods
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = None

        mocker.patch('p_services.models.Product.query', new=mock_query)
        mocker.patch('p_services.view.db.session.commit', return_value=None)
        mocker.patch('p_services.view.db.session.rollback', return_value=None)

        # Mocking lock_manager
        mock_lock = mocker.MagicMock()
        mock_lock.__enter__.return_value = None
        mock_lock.__exit__.return_value = None
        mocker.patch('p_services.view.lock_manager.acquire_lock', return_value=mock_lock)

        # Define the product data
        product_data = {
            "name": "Updated Product",
            "description": "Updated description",
            "price": 100.00,
            "stock": 10,
            "version": 1
        }

        # Call the product endpoint
        response =  client.put('/products/1', json=product_data, headers=headers)
        logging.debug(f"Response received: {response.status_code}")

        # Validate the response
        assert response.status_code == 404
        assert response.json['error'] == 'Product not found'


def test_update_product_conflict(client, mocker):
    # Mock the validate_token function
    with patch('p_services.view.validate_token', side_effect=mock_validate_token):
        logging.debug("Testing product version conflict")

        # Define the headers with the token
        headers = {
            'Authorization': 'Bearer valid-token'
        }

        # Create a mock product with a version conflict
        mock_product = create_mock_product()
        mock_product.version = 2  # Simulate a version conflict

        # Mocking the query methods
        mock_query = mocker.Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_product

        mocker.patch('p_services.models.Product.query', new=mock_query)
        mocker.patch('p_services.view.db.session.commit', return_value=None)
        mocker.patch('p_services.view.db.session.rollback', return_value=None)

        # Mocking lock_manager
        mock_lock = mocker.MagicMock()
        mock_lock.__enter__.return_value = None
        mock_lock.__exit__.return_value = None
        mocker.patch('p_services.view.lock_manager.acquire_lock', return_value=mock_lock)

        # Define the product data
        product_data = {
            "name": "Updated Product",
            "description": "Updated description",
            "price": 100.00,
            "stock": 10,
            "version": 1  # Old version, should cause conflict
        }

        # Call the product endpoint
        response =  client.put('/products/1', json=product_data, headers=headers)
        logging.debug(f"Response received: {response.status_code}")

        # Validate the response
        assert response.status_code == 200
        