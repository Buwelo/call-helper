import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI  = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dev_db')

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False

# Dictionary for easy environment selection
config_dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}
