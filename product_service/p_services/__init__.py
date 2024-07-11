from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from config import Config
import os

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)

    # Explicitly load configuration
    app.config.from_object(config_class)

    # Debug print statements to verify configuration
    print("DATABASE_URL:", os.getenv('DATABASE_URL'))
    print("SQLALCHEMY_DATABASE_URI:", app.config.get('SQLALCHEMY_DATABASE_URI'))

    # Initialize database and migration
    db.init_app(app)
    migrate.init_app(app, db)
    # Register the blueprint
    from .view import product_bp
    app.register_blueprint(product_bp, url_prefix='/api')
    return app
