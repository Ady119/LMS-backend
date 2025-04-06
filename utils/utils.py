from functools import wraps
from flask import request, jsonify, g
from utils.tokens import decode_jwt
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Received Cookies: {request.cookies}")

        token = request.cookies.get("access_token")
        if not token:
            print("No access_token found in cookies")
            return jsonify({"error": "Unauthorized"}), 401

        try:
            decoded = decode_jwt(token)
            g.user = decoded
            print(f"Decoded JWT: {decoded}")
        except Exception as e:
            print(f"JWT Decode Error: {e}")
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    
    return decorated_function

