import os
from datetime import timedelta

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
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_PATH = "/"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

class DevConfig(Config):
    """Development Configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', 'mysql+pymysql://root:@localhost/lms_db')  # Local database

class TestConfig(Config):
    """Testing Configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProdConfig(Config):
    """Production Configuration (for Render deployment)"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SESSION_COOKIE_SECURE = True 

# **Auto-detect environment based on the RENDER_ENV variable**
ENV = os.getenv('FLASK_ENV', 'production').lower()

config_dict = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig
}

# **appropriate configuration**
CurrentConfig = config_dict.get(ENV, ProdConfig)
