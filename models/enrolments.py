from models import db
from sqlalchemy.orm import relationship

class Enrolment(db.Model):
    __tablename__ = 'enrolments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    progress = db.Column(db.Float, default=0.0, nullable=False)

    student = db.relationship("User", backref="enrolments")
    degree = db.relationship("Degree", backref="enrolments")
    
    def __repr__(self):
        return f"<Enrolment Student {self.student_id} Course {self.degree_id}>"
