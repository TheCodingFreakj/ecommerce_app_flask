from functools import wraps
from flask import request, jsonify, current_app
import jwt
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with current_app.app_context():
            from app import db  # Adjust the import based on your project structure

            auth_header = request.headers.get('Authorization')
            if not auth_header:
                logger.error("Token is missing!")
                return jsonify({'message': 'Token is missing!'}), 403

            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                logger.error("Bearer token malformed!")
                return jsonify({'message': 'Bearer token malformed!'}), 403

            try:
                logger.info('Decoding token...')
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                
                # Use connection from the engine
                with db.engine.connect() as connection:
                    query = text('SELECT * FROM "user" WHERE "id" = :user_id')
                    result = connection.execute(query, {'user_id': data['user_id']})
                    current_user = result.fetchone()
                    logger.info(f'Current user: {current_user}')

                    if current_user is None:
                        logger.error("User not found!")
                        return jsonify({'message': 'User not found!'}), 403

            except jwt.ExpiredSignatureError:
                logger.error("Token has expired!")
                return jsonify({'message': 'Token has expired!'}), 403
            except jwt.InvalidTokenError:
                logger.error("Token is invalid!")
                return jsonify({'message': 'Token is invalid!'}), 403

            return f(current_user, *args, **kwargs)
    return decorated


# Admin role decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        with current_app.app_context():
            if not current_user.admin:
                return jsonify({'message': 'Admin access required!'}), 403
            return f(current_user, *args, **kwargs)
    return decorated_function