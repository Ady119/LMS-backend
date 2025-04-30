# config.py
import os
from datetime import timedelta
from sqlalchemy.pool import QueuePool
from urllib.parse import urlparse
import pymysql
pymysql.install_as_MySQLdb()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret_key')

    # JWT settings for flask-jwt-extended
    JWT_TOKEN_LOCATION     = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_COOKIE_SECURE      = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
    JWT_SECRET_KEY         = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": QueuePool,
        "pool_size": 5,
        "max_overflow": 2,
        "pool_timeout": 10
    }

    DROPBOX_ACCESS_TOKEN     = os.getenv("DROPBOX_ACCESS_TOKEN")
    ALLOWED_EXTENSIONS       = {"pdf", "png", "mp4", "txt", "docx"}
    SESSION_TYPE             = 'filesystem'
    SESSION_PERMANENT        = True
    SESSION_USE_SIGNER        = True
    SESSION_COOKIE_SECURE    = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_PATH      = "/"
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

class DevConfig(Config):
    DEBUG = True
    TESTING = False
    JWT_COOKIE_SECURE = False  # allow HTTP in development
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+pymysql://root:@localhost/lms_db2'
    )

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProdConfig(Config):
    DEBUG = False
    raw_db_url = os.getenv('DATABASE_URL')
    if raw_db_url and raw_db_url.startswith("mysql://"):
        raw_db_url = raw_db_url.replace("mysql://", "mysql+pymysql://", 1)
    if raw_db_url:
        parsed_url = urlparse(raw_db_url)
        SQLALCHEMY_DATABASE_URI = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('JAWSDB_URL', 'sqlite:///:memory:')

config_dict = {
    "development": DevConfig,
    "testing":     TestConfig,
    "production":  ProdConfig
}
