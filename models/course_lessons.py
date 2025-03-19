from sqlalchemy.orm import relationship
from models import db

class Lesson(db.Model):
    __tablename__ = "course_lessons"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    course = relationship("Course", back_populates="lessons")
    contents = relationship("LessonSection", back_populates="lesson", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lesson {self.title} (Course ID {self.course_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description if self.description is not None else "",
            "created_at": self.created_at
        }
