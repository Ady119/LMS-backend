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
@app.route('/')
def home():
    return "Welcome to the LMS App!"

env = os.environ.get("FLASK_ENV", "production")
app.config.from_object(config_dict[env])

# Ensure Upload Folder Exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])


CORS(app, resources={r"/*": {"origins": "https://lms-frontend-henna-seven.vercel.app", "supports_credentials": True}})
Session(app)

db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

print("Environment:", os.getenv("FLASK_ENV"))
print("Database URI:", os.getenv("SQLALCHEMY_DATABASE_URI"))

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(lecturer_bp, url_prefix='/api/lecturer')
app.register_blueprint(student_bp, url_prefix='/api/student')


# Use Flask-Migrate Instead of `db.create_all()`
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
