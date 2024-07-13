from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import inspect
from flask import request, jsonify, current_app
import jwt
import logging
from sqlalchemy import text
import asyncio
logger = logging.getLogger(__name__)
# Define the async function to validate the user

def sync_validate_user(user_id, db,app_context):
    with app_context:
        with db.engine.connect() as connection:
            query = text('SELECT * FROM "user" WHERE "id" = :user_id')
            result = connection.execute(query, {'user_id': user_id})
            user = result.fetchone()
            return user
    
# Offload synchronous database operations to a separate thread using ThreadPoolExecutor to avoid blocking the main event loop.
executor = ThreadPoolExecutor(max_workers=5)

async def async_validate_user(user_id, db):
    loop = asyncio.get_event_loop()
    app_context = current_app.app_context()
    user = await loop.run_in_executor(executor, sync_validate_user, user_id, db,app_context)
    return user
def token_required(f):
    @wraps(f)
    async def decorated_async(*args, **kwargs):
        from app import db
        auth_header = request.headers.get('Authorization')
        current_app.logger.error(f"auth_header-----------> {auth_header}")
        
        if not auth_header:
            current_app.logger.error("Token is missing!")
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            # Split and retrieve the token
            token = auth_header.split(" ")[1]
            current_app.logger.info(token)
        except IndexError:
            current_app.logger.error("Bearer token malformed!")
            return jsonify({'message': 'Bearer token malformed!'}), 403

        try:
            current_app.logger.info('Decoding token...')
            # Decode the JWT token
            current_app.logger.info(token)
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_app.logger.info(data)

            # Use asyncio to validate the user asynchronously
            current_user = await async_validate_user(data['user_id'], db)
            if current_user is None:
                current_app.logger.error("User not found!")
                return jsonify({'message': 'User not found!'}), 403

        except jwt.ExpiredSignatureError:
            current_app.logger.error("Token has expired!")
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            current_app.logger.error("Token is invalid!")
            return jsonify({'message': 'Token is invalid!'}), 403
        except Exception as e:
            current_app.logger.error(f"Error during token validation: {str(e)}")
            return jsonify({'message': 'Token validation failed!'}), 500

        return await f(current_user, *args, **kwargs)
    
    @wraps(f)
    def decorated_sync(*args, **kwargs):
        from app import db
        auth_header = request.headers.get('Authorization')
        current_app.logger.error(f"auth_header-----------> {auth_header}")
        
        if not auth_header:
            current_app.logger.error("Token is missing!")
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            # Split and retrieve the token
            token = auth_header.split(" ")[1]
            current_app.logger.info(token)
        except IndexError:
            current_app.logger.error("Bearer token malformed!")
            return jsonify({'message': 'Bearer token malformed!'}), 403

        try:
            current_app.logger.info('Decoding token...')
            # Decode the JWT token
            current_app.logger.info(token)
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_app.logger.info(data)

            # Use asyncio to validate the user asynchronously
            current_user = asyncio.run(async_validate_user(data['user_id'], db))

            current_app.logger.info(f'current_user------------------> {current_user}')
            if current_user is None:
                current_app.logger.error("User not found!")
                return jsonify({'message': 'User not found!'}), 403

        except jwt.ExpiredSignatureError:
            current_app.logger.error("Token has expired!")
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            current_app.logger.error("Token is invalid!")
            return jsonify({'message': 'Token is invalid!'}), 403
        except Exception as e:
            current_app.logger.error(f"Error during token validation: {str(e)}")
            return jsonify({'message': 'Token validation failed!'}), 500

        return f(current_user, *args, **kwargs)
    
    if inspect.iscoroutinefunction(f):
        return decorated_async
    else:
        return decorated_sync