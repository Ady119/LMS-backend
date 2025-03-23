import os
from datetime import timedelta
from sqlalchemy.pool import QueuePool
from urllib.parse import urlparse
import pymysql
pymysql.install_as_MySQLdb()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret_key')      
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/lms_db2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": QueuePool,
        "pool_size": 5,
        "max_overflow": 2,
        "pool_timeout": 10
    }
    
    # Dropbox API Token (Set in Heroku)
    DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

    ALLOWED_EXTENSIONS = {"pdf", "jpg", "png", "mp4", "zip", "txt", "docx"}  

    # Session Configuration (Keep the same)
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
    DEBUG = True

class TestConfig(Config):
    """Testing Configuration"""
    TESTING = True


class ProdConfig(Config):
    """Production Configuration (for Heroku deployment)"""
    DEBUG = False

    # Use DATABASE_URL for Heroku MySQL config
    raw_db_url = os.getenv('DATABASE_URL')

    if raw_db_url:
        # Ensure correct format for MySQL on Heroku
        if raw_db_url.startswith("mysql://"):
            raw_db_url = raw_db_url.replace("mysql://", "mysql+pymysql://", 1)
        
        # Parse and reconstruct database URL to prevent errors
        parsed_url = urlparse(raw_db_url)
        SQLALCHEMY_DATABASE_URI = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('JAWSDB_URL', 'sqlite:///:memory:')



# Auto-detect environment based on the FLASK_ENV environment variable
ENV = os.getenv('FLASK_ENV', 'production').lower()

config_dict = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig
}

# Get the appropriate configuration
CurrentConfig = config_dict.get(ENV, ProdConfig)
