from models import db
from sqlalchemy.orm import relationship

class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    degree_id = db.Column(db.Integer, db.ForeignKey("degrees.id"), nullable=True)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    institution = relationship("Institution", back_populates="courses")  
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    degree = relationship("Degree", back_populates="courses")
    exams = relationship("Exam", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course {self.title} (Institution ID {self.institution_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "institution_id": self.institution_id,
            "degree_id": self.degree_id,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at
        }
