from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.users import User
from models import db
from flask import jsonify, make_response
from utils.tokens import get_jwt_token, decode_jwt
from flask_cors import CORS, cross_origin

auth_bp = Blueprint('auth_bp', __name__)

# CORS for Blueprint
@auth_bp.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = [
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "https://lms-frontend-henna-sigma.vercel.app"
    ]

    return response


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username_or_email")
    password = data.get("password")
    print(f"Received username: {username}, password: {password}")
    data = request.get_json()
    print(f"Received Data: {data}")  # Add more logging to verify incoming data

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    #Generate JWT token
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
        samesite="Lax",
        path="/",
        partitioned=True,
        max_age=86400
    )
    
    return response


@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"message": "Logout successful"}))
    
    response.set_cookie(
        "access_token", "", 
        httponly=True, 
        secure=False,  
        samesite="None",  
        path="/",
        partitioned=True,
        max_age=0
    )

    return response


#register Route
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

    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
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



@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    # Get the access_token from the cookies
    token = request.cookies.get("access_token")
    
    # If there's no token, return an error message
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # Try to decode the JWT token
        decoded_token = decode_jwt(token)
        
        # If decoding fails, it will raise an exception, so we return an error
        if not decoded_token:
            return jsonify({"error": "Invalid or expired token"}), 401

        print("Decoded JWT:", decoded_token)

        # Return user details if authenticated successfully
        return jsonify({
            "message": "Authenticated",
            "user": {
                "id": decoded_token.get("user_id"),
                "role": decoded_token.get("role"),
                "username_or_email": decoded_token.get("username_or_email"),
                "institution_id": decoded_token.get("institution_id")
            }
        }), 200
    except Exception as e:
        # Catch any unexpected errors during decoding
        print(f"Error decoding token: {str(e)}")
        return jsonify({"error": "Invalid or expired token"}), 401

