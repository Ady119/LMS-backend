from flask import jsonify, request, g
import datetime
from config import Config
import jwt

SECRET_KEY = Config.SECRET_KEY 

def get_jwt_token(user_data):
    """Generate JWT token with user payload"""
    if not user_data:
        raise ValueError("User data must be provided to generate JWT token")

    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    payload = {"exp": expiration, **user_data}

    print("🚀 JWT Payload before encoding:", payload)

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def decode_jwt(token):
    """Decode and validate JWT token and store user in `g`."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print("Decoded JWT Payload:", payload)
        g.user = payload
        return payload
    except jwt.ExpiredSignatureError:
        print("Token Expired")
        return None 
    except jwt.InvalidTokenError:
        print("Invalid Token Provided")
        return None