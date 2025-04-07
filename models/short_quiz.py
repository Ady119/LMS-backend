from models import db

class ShortAnswerQuestion(db.Model):
    __tablename__ = "short_answer_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)

    from models.quizzes import Quiz
    quiz = db.relationship("Quiz", back_populates="short_answer_questions")

    def to_dict(self):
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "question_text": self.question_text,
            "correct_answer": self.correct_answer,
            "type": "short"
        }

