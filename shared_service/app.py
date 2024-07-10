import os
from flask import Flask, request, jsonify
from decorators import token_required  # Ensure this path is correct
from config import Config
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS 
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy()
db.init_app(app)
CORS(app)
@app.route('/validate_token', methods=['POST'])
@token_required
def validate_token(current_user):
    return jsonify({"user_id": current_user.id, "username": current_user.username})

if __name__ == '__main__':
    app.run(debug=True)

