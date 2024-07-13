
import asyncio
from flask import request, jsonify
from flask import Blueprint, current_app, request, jsonify, make_response
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


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Retrieve the Authorization header
        auth = request.headers.get('Authorization')

        # Check if the Authorization header is present
        if not auth:
            current_app.logger.warning("Unauthorized access attempt without token.")
            return jsonify({'error': 'Unauthorized access'}), 403

        token = auth
        validation_response = None

        current_user = None

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            validation_response = loop.run_until_complete(validate_token(token))
            if 'username' in validation_response:
                current_user = validation_response
            else:
                raise   
        except Exception as e:
            current_app.logger.error(f"Error during token validation: {str(e)}")
            return jsonify({'error': 'Token validation failed'}), 500
        finally:
            loop.close()

        current_app.logger.info(f"Token validated successfully for user: {validation_response}")

        return f(*args, validation_response=current_user, **kwargs)

    return decorated

@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Retrieve the details of a specific product by product_id.
    """
    try:
        # Log the start of the request handling
        current_app.logger.info(f"Fetching product with ID: {product_id}")

        # Retrieve the product from the database
        product = Product.query.get(product_id)

        if product:
            # Log successful retrieval
            current_app.logger.info(f"Product found: {product.to_dict()}")
            return jsonify(product.to_dict()), 200
        else:
            # Log product not found
            current_app.logger.warning(
                f"Product with ID {product_id} not found.")
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        # Log any exceptions that occur
        current_app.logger.error(f"An error occurred while fetching product with ID {product_id}: {str(e)}")

        return jsonify({'error': 'An error occurred while fetching the product'}), 500


@product_bp.route('/products', methods=['POST'])
@token_required
def create_product(validation_response):
    """
    Create a new product. 
    The user must be authenticated to create a product.
    """
    with current_app.app_context():
        current_user = validation_response
        current_app.logger.info(f"Current user: {current_user['username']}")

        # Get the data from the request
        data = request.get_json()

        try:
            # Log the received data
            current_app.logger.info(f"Data received for new product: {data}")

            # Create new product instance
            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                stock=data['stock'],
                last_modified_by=current_user["user_id"],
                version=1
            )

            # Add the new product to the database session
            db.session.add(new_product)
            db.session.commit()
            current_app.logger.info(
                f"Product created with ID: {new_product.id}")

            # Return the created product as a JSON response
            return jsonify(new_product.to_dict()), 201

        except IntegrityError as e:
            # Rollback the session in case of an integrity error (e.g., duplicate product name)
            db.session.rollback()
            current_app.logger.warning(f"Integrity error: {str(e)}")
            return jsonify({'error': 'Product with this name already exists. Please use a different name.'}), 409

        except SQLAlchemyError as e:
            # Rollback the session in case of other SQLAlchemy errors
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error: {str(e)}")
            return jsonify({'error': str(e)}), 500


def update_product_stock(product_id, data, current_user):
    """
    Helper function to update the stock or details of a product.
    Uses a lock to ensure consistency and avoid race conditions.
    """
    with lock_manager.acquire_lock(product_id):
        try:
            # Retrieve the product from the database with a lock
            product = Product.query.filter_by(
                id=product_id).with_for_update().first()
            if not product:
                current_app.logger.warning(
                    f"Product with ID {product_id} not found.")
                return jsonify({'error': 'Product not found'}), 404

            # Check if the current user is the last modifier of the product
            if current_user["user_id"] == product.last_modified_by:
                current_app.logger.info(
                    f"User {current_user['username']} is the last modifier. Proceeding with update.")

                # Update product information
                product.name = data['name']
                product.description = data['description']
                product.price = data['price']
                product.stock = data['stock']
                product.version += 1  # Increment version
                product.last_modified_by = current_user["user_id"]

                db.session.commit()
                current_app.logger.info(
                    f"Product {product_id} updated successfully by user {current_user['username']}."
                )
                return jsonify(product.to_dict()), 200
            else:
                # Check for version conflict
                if product.version != data['version']:
                    current_app.logger.warning(
                        f"Version conflict for product {product_id}. Expected version: {data['version']}, actual version: {product.version}."
                    )
                    return jsonify({'error': 'Product has been updated by another user. Please refresh and try again.'}), 409
                else:
                    current_app.logger.info(
                        f"No version conflict detected for product {product_id}. Proceeding with update."
                    )

                    # Update product information
                    product.name = data['name']
                    product.description = data['description']
                    product.price = data['price']
                    product.stock = data['stock']
                    product.version += 1  # Increment version
                    product.last_modified_by = current_user["user_id"]

                    db.session.commit()
                    current_app.logger.info(f"Product {product_id} updated successfully by user {current_user['username']}.")
                    return jsonify(product.to_dict()), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error while updating product {product_id}: {str(e)}")
            return jsonify({'error': str(e)}), 500


@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(product_id, validation_response):
    """
    Update the stock or details of an existing product. 
    The user must be authenticated to update a product.
    """
    with current_app.app_context():
        current_user = validation_response
        current_app.logger.info(f"Current user: {current_user['username']}")

        # Get the data from the request
        data = request.get_json()
        current_app.logger.info(f"Data received for updating product {product_id}: {data}")
        
        try:
            #check if the product already is present
            existing_product = Product.query.filter_by(name=data.get('name')).first()
            if existing_product:
                return jsonify({'message': 'Product already exists'}), 404
            # Call the function to update the product stock or details
            response = update_product_stock(product_id, data, current_user)
            current_app.logger.info(
                f"Product {product_id} updated successfully.")
            return response
        except SQLAlchemyError as e:
            # Rollback the session in case of SQLAlchemy errors
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error while updating product {product_id}: {str(e)}")
            return jsonify({'error': str(e)}), 500


def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Product.to_dict = to_dict
