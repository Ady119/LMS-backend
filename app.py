import os
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from flask_migrate import Migrate
from flask_session import Session
from dotenv import load_dotenv
from config import config_dict

from models import db
from routes.authentication import auth_bp
from routes.super_admin import admin_bp
from routes.lecturers import lecturer_bp
from routes.students import student_bp

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

env = os.environ.get("FLASK_ENV", "development")
app.config.from_object(config_dict[env])

# Ensure Upload Folder Exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

Session(app)
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:4173",  # Your frontend running at port 4173
    "http://127.0.0.1:4173",  # Explicit IP version for localhost
    "http://localhost:5173",  # Another possible frontend URL
    "http://127.0.0.1:5173",  # Explicit IP for port 5173
]}}, supports_credentials=True)

db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(lecturer_bp, url_prefix='/api/lecturer')
app.register_blueprint(student_bp, url_prefix='/api/student')

# Use Flask-Migrate Instead of `db.create_all()`
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
