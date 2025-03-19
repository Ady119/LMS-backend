from models import db
from models.lessons import Lesson
from models.sections import Section

class ProgressManager:
    @staticmethod
    def update_lesson_progress(enrolment, lesson_id):
        """Update lesson progress based on completed sections."""
        # Fetch the lesson and its sections
        lesson = Lesson.query.filter_by(id=lesson_id).first()
        if not lesson:
            raise ValueError("Lesson not found")

        lesson_sections = Section.query.filter_by(lesson_id=lesson.id).all()
        total_sections = len(lesson_sections)
        completed_sections = [
            section.id for section in lesson_sections if section.id in enrolment.completed_sections
        ]

        # Calculate lesson progress
        lesson_progress = (len(completed_sections) / total_sections) * 100 if total_sections > 0 else 0
        is_lesson_completed = len(completed_sections) == total_sections

        return {
            "lesson_id": lesson_id,
            "lesson_progress": lesson_progress,
            "is_lesson_completed": is_lesson_completed
        }

    @staticmethod
    def update_course_progress(enrolment):
        """Update course progress based on completed lessons."""
        # Fetch lessons in the course
        lessons = Lesson.query.filter_by(course_id=enrolment.course_id).all()
        total_lessons = len(lessons)
        completed_lessons = 0

        for lesson in lessons:
            # Check if all sections in the lesson are completed
            lesson_sections = Section.query.filter_by(lesson_id=lesson.id).all()
            if all(section.id in enrolment.completed_sections for section in lesson_sections):
                completed_lessons += 1

        # Calculate course progress
        course_progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
        enrolment.progress = course_progress
        enrolment.is_completed = completed_lessons == total_lessons

        db.session.commit()

        return {
            "course_id": enrolment.course_id,
            "course_progress": course_progress,
            "is_course_completed": enrolment.is_completed
        }
