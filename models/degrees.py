from models import db
from sqlalchemy.orm import relationship

class Degree(db.Model):
    __tablename__ = "degrees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey("academic_calendars.id"), nullable=True)
    
    calendar = relationship("AcademicCalendar", back_populates="degrees")
    institution = relationship("Institution", back_populates="degrees")
    courses = relationship("Course", back_populates="degree", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Degree {self.name} (Institution ID {self.institution_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "institution_id": self.institution_id,
            "calendar_id": self.calendar_id,
        }
