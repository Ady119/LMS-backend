import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, send_file, request
from flask_mail import Mail
from flask_cors import CORS
from flask_migrate import Migrate
from flask_session import Session

from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

from config import config_dict
from models import db
from routes.authentication import auth_bp
from routes.super_admin    import admin_bp
from routes.lecturers      import lecturer_bp
from routes.students       import student_bp
from routes.chat           import chat_bp

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the LMS App!"

env = os.environ.get("FLASK_ENV", "production")
app.config.from_object(config_dict[env])

app.config["JWT_TOKEN_LOCATION"]     = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_COOKIE_SECURE"]      = True
app.config["JWT_COOKIE_SAMESITE"]    = "None"
jwt = JWTManager(app)

CORS(app, resources={ r"/*": {
    "origins": [
        "https://lms-frontend-henna-sigma.vercel.app",
        "https://lms-frontend-5v355z5s0-adrians-projects-6add6cfa.vercel.app",
        "https://lms-frontend-git-feature-offli-aed0ff-adrians-projects-6add6cfa.vercel.app",
    ],
    "supports_credentials": True
}})
Session(app)

db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

socketio = SocketIO(
    app,
    async_mode="eventlet",
    cors_allowed_origins=[
        "https://lms-frontend-henna-sigma.vercel.app",
        "https://lms-frontend-5v355z5s0-adrians-projects-6add6cfa.vercel.app",
        "https://lms-frontend-git-feature-offli-aed0ff-adrians-projects-6add6cfa.vercel.app",
    ],
    manage_session=False
)
@socketio.on("connect")
def on_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    print(f"Client disconnected: {request.sid}")

# register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(lecturer_bp, url_prefix='/api/lecturer')
app.register_blueprint(student_bp, url_prefix='/api/student')
app.register_blueprint(chat_bp, url_prefix='/api/chat')

if __name__ == '__main__':
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config['DEBUG']
    )
