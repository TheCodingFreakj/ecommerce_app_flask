import os

basedir = os.path.abspath(os.path.dirname(__file__))
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_timeout': 20,
        'pool_pre_ping': True
    }
    