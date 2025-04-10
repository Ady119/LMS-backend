from models import db
import os
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submissions"
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    original_file_name = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=func.current_timestamp())

    assignment = relationship("Assignment", backref=db.backref("submissions", cascade="all, delete-orphan"))

    student = relationship("User", backref="assignment_submissions")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "student_id": self.student_id,
            "file_name": self.original_file_name or os.path.basename(self.file_url),
            "file_url": self.file_url,
            "submitted_at": self.submitted_at.isoformat()
        }
