from models import db
from sqlalchemy.orm import relationship

class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    total_marks = db.Column(db.Integer, nullable=False)

    course = relationship("Course", back_populates="exams")

    def __repr__(self):
        return f"<Exam {self.title} (Course ID {self.course_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "total_marks": self.total_marks
        }
