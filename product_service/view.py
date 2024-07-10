from flask import request, jsonify
from flask import Blueprint, current_app, request, jsonify, make_response
import datetime
from functools import wraps
import logging
from .models import Product
from .models import db

from sqlalchemy.exc import SQLAlchemyError, IntegrityError


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Create a blueprint for the user routes
product_bp = Blueprint('product', __name__)


@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({'error': 'Product not found'}), 404


@product_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    try:
        # Create new product instance
        new_product = Product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            stock=data['stock'],
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


@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    try:
        product = Product.query.filter_by(
            id=product_id).with_for_update().first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Check for version conflict
        if product.version != data['version']:
            return jsonify({'error': 'Product has been updated by another user. Please refresh and try again.'}), 409

        # Update product information
        product.name = data['name']
        product.description = data['description']
        product.price = data['price']
        product.stock = data['stock']
        product.version += 1  # Increment version

        db.session.commit()
        return jsonify(product.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Product.to_dict = to_dict
