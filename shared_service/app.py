import os
from flask import Flask, request, jsonify
from auth_utils import token_required
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/validate_token', methods=['POST'])
@token_required
def validate_token(value):
    return jsonify({"user_id": value})
# def validate_token(current_user):
#     return jsonify({"user_id": current_user.id, "username": current_user.username})

if __name__ == '__main__':
    if not app.config['SECRET_KEY']:
        print("SECRET_KEY environment variable not set!")
    app.run(debug=True)