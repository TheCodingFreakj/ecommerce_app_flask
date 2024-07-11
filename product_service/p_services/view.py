
import asyncio
from flask import request, jsonify
from flask import Blueprint, current_app, request, jsonify, make_response
import datetime
from functools import wraps
import logging

from . import lock_manager

from .client import validate_token
from .models import Product
from .models import db

from sqlalchemy.exc import SQLAlchemyError, IntegrityError


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
product_bp = Blueprint('product', __name__)

# or auth != 'Bearer your_secret_token'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')

        if not auth:
            return jsonify({'error': 'Unauthorized access'}), 403

        token = auth
        loop = asyncio.get_event_loop()
        if loop.is_running():
            data = asyncio.run_coroutine_threadsafe(
                validate_token(token), loop).result()
        else:
            data = loop.run_until_complete(validate_token(token))
        validation_response = data
        return f(*args, validation_response=validation_response, **kwargs)
    return decorated


@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({'error': 'Product not found'}), 404


@product_bp.route('/products', methods=['POST'])
@token_required
def create_product(validation_response):
    with current_app.app_context():
        if 'user_id' not in validation_response:
            return jsonify({'message': 'Token is invalid!'}), 403
        current_user = validation_response
        data = request.get_json()
        try:
            # Create new product instance
            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                stock=data['stock'],
                last_modified_by=current_user["user_id"],
                version=1
            )

            db.session.add(new_product)
            db.session.commit()
            return jsonify(new_product.to_dict()), 201

        except IntegrityError as e:
            db.session.rollback()
            return jsonify({'error': 'Product with this name already exists. Please use a different name.'}), 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


def update_product_stock(product_id, data, current_user):
    with lock_manager.acquire_lock(product_id):
        product = Product.query.filter_by(
            id=product_id).with_for_update().first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if (current_user["user_id"] == product.last_modified_by):
            # Update product information
            product.name = data['name']
            product.description = data['description']
            product.price = data['price']
            product.stock = data['stock']
            product.version += 1  # Increment version
            product.last_modified_by = current_user["user_id"]

            db.session.commit()
            return jsonify(product.to_dict()), 200
        else:
            # Check for version conflict
            if product.version != data['version']:
                return jsonify({'error': 'Product has been updated by another user. Please refresh and try again.'}), 409
            else:
                product.name = data['name']
                product.description = data['description']
                product.price = data['price']
                product.stock = data['stock']
                product.version += 1  # Increment version
                product.last_modified_by = current_user["user_id"]

                db.session.commit()
                return jsonify(product.to_dict()), 200


@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(product_id, validation_response):

    with current_app.app_context():
        if 'user_id' not in validation_response:
            return jsonify({'message': 'Token is invalid!'}), 403
        current_user = validation_response

        data = request.get_json()
        try:
            return update_product_stock(product_id, data, current_user)
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Product.to_dict = to_dict
