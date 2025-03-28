from models import db
from sqlalchemy.orm import relationship
from classes.validators import validate_age, validate_length
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'lecturer', 'admin'
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)
    date_created = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    
    quizzes = db.relationship("Quiz", back_populates="lecturer", cascade="all, delete")

    def set_password(self, password):
        """Hashes the password before storing."""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        """Checks if a given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "institution_id": self.institution_id,
            "date_created": self.date_created,
            }