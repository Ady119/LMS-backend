from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from models.users import User
from models import db
from utils.tokens import get_jwt_token, decode_jwt

auth_bp = Blueprint('auth_bp', __name__)

# CORS for Blueprint
@auth_bp.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://lms-frontend-5v355z5s0-adrians-projects-6add6cfa.vercel.app",
        "https://lms-frontend-git-feature-offli-aed0ff-adrians-projects-6add6cfa.vercel.app",
        "https://lms-frontend-henna-sigma.vercel.app"
    ]

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response

# Login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username_or_email")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = get_jwt_token({
        "user_id": user.id,
        "username_or_email": user.username,
        "role": user.role,
        "institution_id": user.institution_id
    })

    response = make_response(jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "role": user.role,
            "username": user.username,
            "email": user.email
        }
    }))

    response.set_cookie(
        "access_token", token,
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
        max_age=86400
    )

    return response

# Logout
@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"message": "Logout successful"}))

    response.set_cookie(
        "access_token", "",
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
        max_age=0
    )

    return response

# Register
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'student')

    if not username or not email or not password or not full_name:
        return jsonify({"error": "All fields are required"}), 400

    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201

# Auth Check
@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    token = request.cookies.get("access_token")

    if not token:
        print("No token found in cookies")
        return jsonify({"error": "Not authenticated"}), 401

    try:
        decoded_token = decode_jwt(token)
        if not decoded_token:
            return jsonify({"error": "Invalid or expired token"}), 401
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return jsonify({"error": "Invalid token"}), 401

    return jsonify({
        "message": "Authenticated",
        "user": {
            "id": decoded_token.get("user_id"),
            "role": decoded_token.get("role"),
            "username_or_email": decoded_token.get("username_or_email"),
            "institution_id": decoded_token.get("institution_id")
        }
    }), 200
