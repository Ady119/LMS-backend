from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User.query.filter_by(username="testuser").first()
    if user:
        user.password_hash = generate_password_hash("password123", method='pbkdf2:sha256', salt_length=16)
        db.session.commit()
        print("Password updated successfully!")
    else:
        print("User not found!")
