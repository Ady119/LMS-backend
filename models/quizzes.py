from models import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    max_attempts = db.Column(db.Integer, nullable=True, default=3)
    time_limit = db.Column(db.Integer, nullable=True)
    randomize_questions = db.Column(db.Boolean, nullable=False, default=False)
    immediate_feedback = db.Column(db.Boolean, nullable=False, default=False)
    passing_score = db.Column(db.Float, nullable=True, default=50.0)
    deadline = db.Column(db.DateTime, nullable=True)

    lecturer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    lecturer = db.relationship("User", back_populates="quizzes")

    questions = db.relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")

    @property
    def total_questions(self):
        return len(self.questions)

    def __repr__(self):
        return f"<Quiz {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "max_attempts": self.max_attempts,
            "time_limit": self.time_limit,
            "randomize_questions": self.randomize_questions,
            "immediate_feedback": self.immediate_feedback,
            "passing_score": self.passing_score,
            "deadline": (
                datetime.fromisoformat(self.deadline).isoformat()
                if isinstance(self.deadline, str) and self.deadline.strip()
                else (self.deadline.isoformat() if isinstance(self.deadline, datetime) else None)
            ),
            "lecturer_id": self.lecturer_id,
            "questions": [q.to_dict() for q in self.questions],
        }
