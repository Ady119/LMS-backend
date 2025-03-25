from models import db
from datetime import datetime

class SectionProgress(db.Model):
    __tablename__ = "section_progress"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey("lesson_section.id"), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("student_id", "section_id", name="unique_student_section"),
    )
