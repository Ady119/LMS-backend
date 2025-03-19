from models import db
from datetime import datetime

class QuizResult(db.Model):
    __tablename__ = "quiz_results"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempts.id"), nullable=False)
    score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempt = db.relationship("QuizAttempt", back_populates="result")
    
    def to_dict(self):
        return {
            "id": self.id,
            "attempt_id": self.attempt_id,
            "score": self.score,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat(),
        }
