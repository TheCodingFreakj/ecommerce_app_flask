from flask import Blueprint, current_app, request, jsonify, make_response
import datetime
from functools import wraps
import logging
from .models import Order, OrderItem
from .models import db








logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Create a blueprint for the user routes
order_bp = Blueprint('order', __name__)


@order_bp.route('/create-orders', methods=['POST'])
def create_order():
    data = request.get_json()
    order_items = data.get('items', [])
    total_price = sum(item['price'] * item['quantity'] for item in order_items)

    new_order = Order(
        customer_name=data['customer_name'],
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