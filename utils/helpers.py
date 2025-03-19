from models import db


def format_datetime(datetime_obj):
    """Format datetime to a readable string."""
    if not datetime_obj:
        return None
    return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

def quiz_questions_json(questions):
    """
    Convert a list of question dictionaries into JSON format.
    """
    import json
    try:
        return json.dumps(questions)
    except Exception as e:
        raise ValueError(f"Error building quiz JSON: {e}")

def validate_questions(questions):
    if not isinstance(questions, list):
        raise ValueError("Questions must be a list.")
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("Each question must be a dictionary.")
        if "question" not in question or "options" not in question or "correct_answer" not in question:
            raise ValueError("Each question must have 'question', 'options', and 'correct_answer'.")
        if not isinstance(question['options'], list):
            raise ValueError("'options' must be a list.")
        if question['correct_answer'] not in question['options']:
            raise ValueError("The 'correct_answer' must be one of the options.")
        
@property
def is_late(self):
    if self.assignment.due_date and self.submitted_at > self.assignment.due_date:
        return True
    return False

def calculate_course_progress(enrollment_id):
    lessons = LessonProgress.query.filter_by(enrollment_id=enrollment_id).all()
    total_progress = sum(lesson.progress for lesson in lessons) / len(lessons)
    return total_progress

def complete_section(enrollment_id, section_id):
    section_progress = SectionProgress.query.filter_by(
        enrollment_id=enrollment_id,
        section_id=section_id
    ).first()

    if not section_progress:
        section_progress = SectionProgress(
            enrollment_id=enrollment_id,
            section_id=section_id,
            is_completed=True,
            completed_at=db.func.now()
        )
        db.session.add(section_progress)
    else:
        section_progress.is_completed = True
        section_progress.completed_at = db.func.now()

    db.session.commit()

def calculate_lesson_progress(enrollment_id, lesson_id):
    sections = Section.query.filter_by(lesson_id=lesson_id).all()
    total_sections = len(sections)
    completed_sections = SectionProgress.query.filter_by(
        enrollment_id=enrollment_id,
        is_completed=True
    ).filter(SectionProgress.section_id.in_([s.id for s in sections])).count()

    return (completed_sections / total_sections) * 100 if total_sections > 0 else 0

def check_prerequisite(enrollment_id, section_id):
    section = Section.query.get(section_id)
    if section.prerequisite_id:
        prerequisite_progress = SectionProgress.query.filter_by(
            enrollment_id=enrollment_id,
            section_id=section.prerequisite_id,
            is_completed=True
        ).first()
        return prerequisite_progress is not None
    return True

def calculate_lesson_progress(enrollment_id, lesson_id):
    # Fetch all sections in the lesson
    sections = Section.query.filter_by(lesson_id=lesson_id).all()
    total_sections = len(sections)

    # Count completed sections
    completed_sections = SectionProgress.query.filter_by(
        enrollment_id=enrollment_id,
        is_completed=True
    ).filter(SectionProgress.section_id.in_([s.id for s in sections])).count()

    # Calculate progress percentage
    progress = (completed_sections / total_sections) * 100 if total_sections > 0 else 0

    # Update LessonProgress
    lesson_progress = LessonProgress.query.filter_by(
        enrollment_id=enrollment_id,
        lesson_id=lesson_id
    ).first()

    if not lesson_progress:
        lesson_progress = LessonProgress(
            enrollment_id=enrollment_id,
            lesson_id=lesson_id,
            progress=progress,
            is_completed=(progress == 100)
        )
        db.session.add(lesson_progress)
    else:
        lesson_progress.progress = progress
        lesson_progress.is_completed = (progress == 100)

    db.session.commit()

def calculate_course_progress(enrollment_id, course_id):
    # Fetch all lessons in the course
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    total_lessons = len(lessons)

    # Count completed lessons
    completed_lessons = LessonProgress.query.filter_by(
        enrollment_id=enrollment_id,
        is_completed=True
    ).filter(LessonProgress.lesson_id.in_([l.id for l in lessons])).count()

    # Calculate progress percentage
    progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0

    # Update Enrollment
    enrollment = Enrollment.query.filter_by(id=enrollment_id).first()
    enrollment.progress = progress
    enrollment.is_completed = (progress == 100)

    db.session.commit()

def add_grade(enrollment_id, item_type, item_id, grade, feedback=None):
    new_grade = Grade(
        enrollment_id=enrollment_id,
        graded_item_type=item_type,
        graded_item_id=item_id,
        grade=grade,
        feedback=feedback
    )
    db.session.add(new_grade)
    db.session.commit()

    
def add_grade(enrollment_id, item_type, item_id, grade, feedback=None):
    new_grade = Grade(
        enrollment_id=enrollment_id,
        graded_item_type=item_type,
        graded_item_id=item_id,
        grade=grade,
        feedback=feedback
    )
    db.session.add(new_grade)
    db.session.commit()

def create_course_notification(course_id, title, message, notification_type="announcement"):
    notification = Notification(
        course_id=course_id,
        title=title,
        message=message,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

def create_user_notification(user_id, title, message, notification_type="message"):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

def get_course_notifications(course_id):
    notifications = Notification.query.filter_by(course_id=course_id).order_by(Notification.created_at.desc()).all()
    return [notification.to_dict() for notification in notifications]

def mark_notification_as_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and not notification.is_read:
        notification.is_read = True
        db.session.commit()
