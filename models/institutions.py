from models import db
from sqlalchemy.orm import relationship

class Institution(db.Model):
    __tablename__ = 'institutions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    
    degrees = relationship("Degree", back_populates="institution", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="institution", cascade="all, delete-orphan")
    users = relationship('User', backref='institution', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Institution {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at
        }
