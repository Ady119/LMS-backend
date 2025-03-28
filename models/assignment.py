from models import db
from sqlalchemy.orm import relationship

class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    dropbox_path = db.Column(db.String(255), nullable=True)

    sections = relationship("LessonSection", back_populates="assignment", overlaps="assignment")
    lecturer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lecturer = relationship("User", back_populates="assignments")


    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "file_url": self.file_url,
            "dropbox_path": self.dropbox_path,
            "lecturer_id": self.lecturer_id,
        }
