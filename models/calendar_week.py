from models import db
from sqlalchemy.orm import relationship

class CalendarWeek(db.Model):
    __tablename__ = "calendar_weeks"

    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.Integer, db.ForeignKey("academic_calendars.id"), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    label = db.Column(db.String(100), nullable=False)

    calendar = relationship("AcademicCalendar", back_populates="weeks")
    sections = relationship("LessonSection", back_populates="calendar_week")

    __table_args__ = (
        db.UniqueConstraint('calendar_id', 'week_number', name='uq_calendar_week'),
    )

    def __repr__(self):
        return f"<CalendarWeek {self.label} ({self.start_date} → {self.end_date})>"
