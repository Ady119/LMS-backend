from models import db

class QuizAttemptAnswer(db.Model):
    __tablename__ = "quiz_attempt_answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=True)

    attempt = db.relationship("QuizAttempt", back_populates="answers")

    def to_dict(self):
        return {
            "id": self.id,
            "attempt_id": self.attempt_id,
            "question_id": self.question_id,
            "answer_text": self.answer_text,
            "is_correct": self.is_correct,
        }
