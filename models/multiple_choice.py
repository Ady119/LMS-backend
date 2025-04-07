from models import db

class MultipleChoiceQuestion(db.Model):
    __tablename__ = "multiple_choice_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)

    from models.quizzes import Quiz
    quiz = db.relationship("Quiz", back_populates="multiple_choice_questions")

    def to_dict(self):
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "question_text": self.question_text,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "type": "mcq"
        }

