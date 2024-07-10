import asyncio
from flask import Blueprint, current_app, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask_bcrypt import Bcrypt
import datetime
from functools import wraps
import logging

from .client import validate_token
from .models import User
from .models import db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Create a blueprint for the user routes
user_bp = Blueprint('user', __name__)
# Token decorator



# Register endpoint
@user_bp.route('/register', methods=['POST'])
def register():
    with current_app.app_context():
        bcrypt = Bcrypt()
        data = request.get_json()
        logger.debug('Received registration data: %s', data)
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], password=hashed_password, admin=data.get('admin', False), email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Registered successfully'})

# Login endpoint
@user_bp.route('/login', methods=['POST'])
def login():
    with current_app.app_context():
        bcrypt = Bcrypt()
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if not user or not bcrypt.check_password_hash(user.password, data['password']):
            return make_response('Invalid credentials', 401)

        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.now() + datetime.timedelta(hours=1)}, current_app.config['SECRET_KEY'])
        return jsonify({'token': token})

# Protected route example
@user_bp.route('/protected', methods=['GET'])

def protected():
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
        return jsonify({"message": f"Hello, {current_user['username']}!"})

# # Admin-only route example
# @user_bp.route('/admin', methods=['GET'])
# def admin(current_user):
#     with current_app.app_context():
#        return jsonify({'message': 'Admin access granted'})