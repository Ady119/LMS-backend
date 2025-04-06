import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from flask_migrate import Migrate
from flask_session import Session
from config import config_dict
from models import db
from routes.authentication import auth_bp
from routes.super_admin import admin_bp
from routes.lecturers import lecturer_bp
from routes.students import student_bp

load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the LMS App!"

env = os.environ.get("FLASK_ENV", "production")
app.config.from_object(config_dict[env])
print("Loaded DB URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))
CORS(app, resources={r"/*": {"origins": "https://lms-frontend-henna-sigma.vercel.app", "supports_credentials": True}})
Session(app)

db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

print("Environment:", os.getenv("FLASK_ENV"))
print("Database URI:", os.getenv("SQLALCHEMY_DATABASE_URI"))

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(lecturer_bp, url_prefix='/api/lecturer')
app.register_blueprint(student_bp, url_prefix='/api/student')

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
