from datetime import datetime
from models import db

class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    score = db.Column(db.Float, nullable=True)
    pass_status = db.Column(db.Boolean, nullable=True)
    attempts_used = db.Column(db.Integer, nullable=False, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    needs_review = db.Column(db.Boolean, nullable=False, default=False)
    answers_temp = db.Column(db.JSON, nullable=True)

    quiz = db.relationship("Quiz", backref=db.backref("attempts", lazy=True))
    student = db.relationship("User", backref=db.backref("quiz_attempts", lazy=True))
    answers = db.relationship("QuizAttemptAnswer", back_populates="attempt", lazy=True, cascade="all, delete-orphan")

    result = db.relationship("QuizResult", uselist=False, back_populates="attempt")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "quiz_id": self.quiz_id,
            "score": self.score,
            "pass_status": self.pass_status,
            "attempts_used": self.attempts_used,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "needs_review": self.needs_review,
            "answers_temp": self.answers_temp,
            "answers": [answer.to_dict() for answer in self.answers],
            "result": self.result.to_dict() if self.result else None,
        }
