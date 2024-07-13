import asyncio
from flask import Blueprint, current_app, request, jsonify, make_response
import datetime
from functools import wraps
import logging
from .client import validate_token
from .models import Order, OrderItem
from .models import db


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

order_bp = Blueprint('order', __name__)
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

@order_bp.route('/view-your-orders/<int:order_id>', methods=['POST'])
@token_required
def view_orders(order_id, validation_response):
    """
    View the details of a specific order by order_id. 
    The user must be authenticated and authorized to view the order.
    """
    with current_app.app_context():
        # Check if user_id is present in the validation response
        if 'user_id' not in validation_response:
            current_app.logger.warning("Token is invalid!")
            return jsonify({'message': 'Token is invalid!'}), 403

        current_user = validation_response
        current_app.logger.info(f"Current user: {current_user['username']}")

        # Retrieve the order from the database
        order = Order.query.get(order_id)
        if order:
            # Check if the current user is authorized to view the order
            if order.customer_name == current_user["username"]:
                current_app.logger.info(
                    f"Order {order_id} retrieved successfully for user {current_user['username']}."
                )

                return jsonify(order.to_dict()), 200
            else:
                current_app.logger.warning(
                    f"User {current_user['username']} is not allowed to view order {order_id}.")
                return jsonify({'error': 'You are not allowed to view this order'}), 403
        else:
            current_app.logger.error(f"Order {order_id} not found.")
            return jsonify({'error': 'Order not found'}), 404


@order_bp.route('/create-orders', methods=['POST'])
@token_required
def create_order(validation_response):
    """
    Create a new order based on the provided items. 
    The user must be authenticated to create an order.
    """
    with current_app.app_context():
        # Check if user_id is present in the validation response
        if 'user_id' not in validation_response:
            current_app.logger.warning("Token is invalid!")
            return jsonify({'message': 'Token is invalid!'}), 403

        current_user = validation_response
        current_app.logger.info(f"Current user: {current_user['username']}")

        # Get the data from the request
        data = request.get_json()
        order_items = data.get('items', [])

        # Calculate the total price of the order
        total_price = sum(item['price'] * item['quantity']
                          for item in order_items)
        current_app.logger.info(f"Total price calculated: {total_price}")

        # Create a new order
        new_order = Order(
            customer_name=current_user['username'],
            customer_email=data['customer_email'],
            total_price=total_price
        )
        db.session.add(new_order)
        db.session.commit()
        current_app.logger.info(f"Order created with ID: {new_order.id}")

        # Add items to the order
        for item in order_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
            current_app.logger.info(f"Order item added: {order_item}")

        # Commit all items to the database
        db.session.commit()
        current_app.logger.info(
            f"Order with ID {new_order.id} committed to the database.")

        # Return the created order as a JSON response
        return jsonify(new_order.to_dict()), 201


def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Order.to_dict = to_dict
OrderItem.to_dict = to_dict
