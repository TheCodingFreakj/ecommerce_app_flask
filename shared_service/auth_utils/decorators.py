from functools import wraps
from flask import request, jsonify, current_app
import jwt
import logging
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy

with current_app.app_context():  
  db = SQLAlchemy(current_app)
logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with current_app.app_context():
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'message': 'Token is missing!'}), 403
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Bearer token malformed!'}), 403
            try:
                logger.info(current_app.config['SECRET_KEY'])
                data = jwt.decode(token, 'secret-key', algorithms=["HS256"])
                query = text("SELECT * FROM user WHERE id = :user_id")
                result = db.engine.execute(query, user_id=data['user_id'])
                current_user = result.fetchone()
                logger.info(current_user)
                
                if current_user is None:
                    return jsonify({'message': 'User not found!'}), 403
                
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired!'}), 403
            except jwt.InvalidTokenError:
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