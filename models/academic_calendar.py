from models import db
from sqlalchemy.orm import relationship

class AcademicCalendar(db.Model):
    __tablename__ = "academic_calendars"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    weeks = relationship("CalendarWeek", back_populates="calendar", cascade="all, delete-orphan")
    degrees = relationship("Degree", back_populates="calendar")

    def __repr__(self):
        return f"<AcademicCalendar {self.name}>"
