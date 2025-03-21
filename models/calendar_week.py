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
    is_break = db.Column(db.Boolean, default=False)


    calendar = relationship("AcademicCalendar", back_populates="weeks")
    sections = relationship("LessonSection", back_populates="calendar_week")

    __table_args__ = (
        db.UniqueConstraint('calendar_id', 'week_number', name='uq_calendar_week'),
    )

    def __repr__(self):
        return f"<CalendarWeek {self.label} ({self.start_date} → {self.end_date})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "week_number": self.week_number,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "label": self.label,
            "is_break": self.is_break
        }