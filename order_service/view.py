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
@order_bp.route('/view-your-orders/<int:order_id>', methods=['POST'])
def view_orders(order_id):
    with current_app.app_context():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(validate_token(token))
        validation_response = data
        logger.info(validation_response)
        if 'user_id' not in validation_response:
            return jsonify({'message': 'Token is invalid!'}), 403
        current_user = validation_response

        order = Order.query.get(order_id)
        if order and order.customer_name == current_user["username"]:
            return jsonify(order.to_dict()), 200
        else:
            return jsonify({'error': 'You are not allowed to view this order'}), 404


@order_bp.route('/create-orders', methods=['POST'])
def create_order():
    with current_app.app_context():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(validate_token(token))
        validation_response = data
        logger.info(validation_response)
        if 'user_id' not in validation_response:
            return jsonify({'message': 'Token is invalid!'}), 403
        current_user = validation_response
        data = request.get_json()
        order_items = data.get('items', [])
        total_price = sum(item['price'] * item['quantity'] for item in order_items)

        new_order = Order(
            customer_name=current_user['username'],
            customer_email=data['customer_email'],
            total_price=total_price
        )
        db.session.add(new_order)
        db.session.commit()

        for item in order_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)

        db.session.commit()
        return jsonify(new_order.to_dict()), 201

def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}

Order.to_dict = to_dict
OrderItem.to_dict = to_dict