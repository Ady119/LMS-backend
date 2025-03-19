import os
from datetime import timedelta
import pymysql
pymysql.install_as_MySQLdb()

class Config:
    """Base configuration (applies to all environments)"""
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Get base directory
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads") 
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "png", "mp4", "zip", "txt", "docx"} 

    # Ensure upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret_key')  # Use environment variable for security
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session Configuration
    SESSION_TYPE = 'filesystem'  
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True" if os.getenv('FLASK_ENV', 'production').lower() == 'production' else False
    SESSION_COOKIE_PATH = "/"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)


class DevConfig(Config):
    """Development Configuration"""
    DEBUG = True
    TESTING = False
    # Local database URI
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', 'mysql+pymysql://root:@localhost/lms_db')


class TestConfig(Config):
    """Testing Configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProdConfig(Config):
    """Production Configuration (for Heroku deployment)"""
    DEBUG = False

    # Get database URL from environment variable (Heroku provides this)
    raw_db_url = os.getenv('DATABASE_URL')

    # If it's a MySQL connection (Heroku provides JAWSDB_URL), convert it to pymysql
    if raw_db_url:
        if raw_db_url.startswith("mysql://"):
            raw_db_url = raw_db_url.replace("mysql://", "mysql+pymysql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('JAWSDB_URL')  # Use JawsDB URL if DATABASE_URL isn't found


# Auto-detect environment based on the FLASK_ENV environment variable
ENV = os.getenv('FLASK_ENV', 'production').lower()

config_dict = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig
}

# Get the appropriate configuration
CurrentConfig = config_dict.get(ENV, ProdConfig)
