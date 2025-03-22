from models import db
from datetime import date
from sqlalchemy.orm import relationship
from sqlalchemy import CheckConstraint, func


class LessonSection(db.Model):
    __tablename__ = "lesson_section"

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("course_lessons.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  
    text_content = db.Column(db.Text, nullable=True)  
    file_url = db.Column(db.String(255), nullable=True)  
    order = db.Column(db.Integer, nullable=False, default=1)  
    calendar_week_id = db.Column(db.Integer, db.ForeignKey("calendar_weeks.id"), nullable=True)
    
    @staticmethod
    def get_next_order(lesson_id):
        last_section = LessonSection.query.filter_by(lesson_id=lesson_id).order_by(LessonSection.order.desc()).first()
        return (last_section.order + 1) if last_section else 1
    
    @property
    def is_active(self):
        if not self.calendar_week:
            return True
        return self.calendar_week.start_date <= date.today()

    @property
    def is_current_week(self):
        if not self.calendar_week:
            return False
        today = date.today()
        return self.calendar_week.start_date <= today <= self.calendar_week.end_date

    __table_args__ = (
        CheckConstraint(
            "(quiz_id IS NULL OR assignment_id IS NULL)", 
            name="check_only_one_content_type"
        ),
    )

    lesson = relationship("Lesson", back_populates="contents")
    quiz = relationship("Quiz")
    assignment = relationship("Assignment", back_populates="sections", overlaps="lesson_section")
    calendar_week = relationship("CalendarWeek", back_populates="sections")

    def __repr__(self):
        return f"<LessonSection {self.title} (Lesson ID {self.lesson_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "quiz_id": self.quiz_id,
            "assignment_id": self.assignment_id,
            "title": self.title,
            "content_type": self.content_type,
            "text_content": self.text_content,
            "file_url": self.file_url if self.file_url else None,
            "order": self.order,
            "calendar_week_id": self.calendar_week_id,
            "calendar_week_label": self.calendar_week.label if self.calendar_week else None,
            "is_active": self.is_active,
            "is_current_week": self.is_current_week,
            "calendar_week": {
                "id": self.calendar_week.id,
                "label": self.calendar_week.label,
                "start_date": str(self.calendar_week.start_date),
                "end_date": str(self.calendar_week.end_date),
                "is_break": self.calendar_week.is_break
            } if self.calendar_week else None
        }


