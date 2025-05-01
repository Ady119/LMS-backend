# routes/authentication.py

import os
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import JWTManager
from flask_cors import cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
from models.users import User
from models import db
from utils.tokens import get_jwt_token, decode_jwt

auth_bp = Blueprint('auth_bp', __name__)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "https://lms-frontend-5v355z5s0-adrians-projects-6add6cfa.vercel.app",
    "https://lms-frontend-henna-sigma.vercel.app",
]

@auth_bp.route('/login', methods=['OPTIONS', 'POST'])
@cross_origin(
    origins=ALLOWED_ORIGINS,
    methods=['POST','OPTIONS'],
    allow_headers=['Content-Type','Authorization'],
    supports_credentials=True
)
def login():
    if request.method == 'OPTIONS':
        return make_response('', 200)

    data     = request.get_json() or {}
    username = data.get("username_or_email")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = get_jwt_token({
        "user_id":           user.id,
        "username_or_email": user.username,
        "role":              user.role,
        "institution_id":    user.institution_id
    })

    resp = make_response(jsonify({
        "message": "Login successful",
        "user": {
            "id":       user.id,
            "role":     user.role,
            "username": user.username,
            "email":    user.email
        }
    }), 200)
    resp.set_cookie(
        "access_token", token,
        httponly=True,
        secure=not os.getenv("FLASK_ENV","").startswith("development"),
        samesite="None",
        path="/",
        max_age=86400
    )
    return resp

@auth_bp.route('/logout', methods=['OPTIONS','POST'])
@cross_origin(
    origins=ALLOWED_ORIGINS,
    methods=['POST','OPTIONS'],
    supports_credentials=True
)
def logout():
    if request.method == 'OPTIONS':
        return make_response('', 200)
    resp = make_response(jsonify({"message": "Logout successful"}), 200)
    resp.set_cookie(
        "access_token", "",
        httponly=True,
        secure=not os.getenv("FLASK_ENV","").startswith("development"),
        samesite="None",
        path="/",
        max_age=0
    )
    return resp

@auth_bp.route('/register', methods=['OPTIONS','POST'])
@cross_origin(
    origins=ALLOWED_ORIGINS,
    methods=['POST','OPTIONS'],
    allow_headers=['Content-Type'],
    supports_credentials=True
)
def register():
    if request.method == 'OPTIONS':
        return make_response('', 200)

    data      = request.get_json() or {}
    username  = data.get('username')
    email     = data.get('email')
    password  = data.get('password')
    full_name = data.get('full_name')
    role      = data.get('role', 'student')

    if not (username and email and password and full_name):
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter((User.username==username)|(User.email==email)).first():
        return jsonify({"error": "User already exists"}), 409

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role
    )
    new_user.password_hash = generate_password_hash(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201

@auth_bp.route('/check-auth', methods=['OPTIONS','GET'])
@cross_origin(
    origins=ALLOWED_ORIGINS,
    methods=['GET','OPTIONS'],
    supports_credentials=True
)
def check_auth():
    if request.method == 'OPTIONS':
        return make_response('', 200)

    token = request.cookies.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        decoded = decode_jwt(token)
    except Exception:
        return jsonify({"error": "Invalid or expired token"}), 401

    return jsonify({
        "message": "Authenticated",
        "user": {
            "id":               decoded.get("user_id"),
            "role":             decoded.get("role"),
            "username_or_email":decoded.get("username_or_email"),
            "institution_id":   decoded.get("institution_id")
        }
    }), 200
