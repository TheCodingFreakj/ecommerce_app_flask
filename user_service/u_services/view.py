import asyncio
import re
from flask import Blueprint, current_app, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from . import bcrypt
import datetime
from functools import wraps
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .client import validate_token
from .models import User
from .models import db
import pytz
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Create a blueprint for the user routes
user_bp = Blueprint('user', __name__)
# Token decorator


# Register endpoint
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


@user_bp.route('/register', methods=['POST'])
def register():
    with current_app.app_context():
        data = request.get_json()
        current_app.logger.debug('Received registration data: %s', data)

        # Validate input data
        if not data or 'password' not in data or 'username' not in data or 'email' not in data:
            return jsonify({'message': 'Missing data'}), 400
        if not validate_email(data['email']):
            return jsonify({'message': 'Invalid email format'}), 400
        if len(data['password']) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400

        try:
            # Check if the user already exists
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({'message': 'User with this email already exists'}), 409

            # Hash the password
            hashed_password = bcrypt.generate_password_hash(
                data['password']).decode('utf-8')
            current_app.logger.debug('Hashed password: %s', hashed_password)

            # Create a new user
            new_user = User(username=data['username'], password=hashed_password, admin=data.get(
                'admin', False), email=data['email'])
            current_app.logger.debug('Created new user: %s', new_user)

            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.debug('User added to database and committed')

            return jsonify({'message': 'Registered successfully'}), 200
        except IntegrityError:
            db.session.rollback()
            current_app.logger.error('Database integrity error')
            return jsonify({'message': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Unexpected error: %s', e)
            return jsonify({'message': 'Internal server error'}), 500

# Login endpoint


@user_bp.route('/login', methods=['POST'])
def login():
    with current_app.app_context():
        data = request.get_json()
        current_app.logger.debug('Login data: %s', data)

        # Validate input data
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Missing username or password'}), 400

        try:
            # Query for the user
            user = User.query.filter_by(username=data['username']).first()
            current_app.logger.debug('Found user: %s', user)

            if not user:
                current_app.logger.debug('User not found')
                return jsonify({'message': 'Invalid credentials'}), 401

            # Check the password
            if not bcrypt.check_password_hash(user.password, data['password']):
                current_app.logger.debug('Password check failed')
                return jsonify({'message': 'Invalid credentials'}), 401

            # Generate JWT token
            try:
                local_tz = datetime.datetime.now().astimezone().tzinfo  # Get local time zone
                now = datetime.datetime.now(local_tz)  # Current local time
                utc_now = now.astimezone(pytz.utc)  # Convert current time to UTC
                exp_time = utc_now + datetime.timedelta(hours=1)
                token = jwt.encode({
                    'user_id': user.id,
                    'iat': now,  # issued at time
                    'exp': exp_time  # expiration time
                }, current_app.config['SECRET_KEY'], algorithm='HS256')
                current_app.logger.debug('Generated token: %s', token)
                current_app.logger.debug('Generated token Valid for ------------------>: %s', exp_time)
                return jsonify({'token': token}), 200
            except Exception as e:
                current_app.logger.error('Token generation failed: %s', e)
                return jsonify({'message': 'Token generation failed'}), 500

        except SQLAlchemyError as e:
            current_app.logger.error('Database error: %s', e)
            return jsonify({'message': 'Database error'}), 500
        except Exception as e:
            current_app.logger.error('Unexpected error: %s', e)
            return jsonify({'message': 'Internal server error'}), 500

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
