from models import db, Badge, UserBadge, SectionProgress, QuizAttempt
from sqlalchemy import func
from models.assignment import Assignment
from models.assignment_submission import AssignmentSubmission
from models.courses import Course
from models.course_lessons import Lesson
from models.lesson_section import LessonSection
from models.section_progress import SectionProgress



def award_badge(student_id, badge_name):
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge:
        return

    already_awarded = UserBadge.query.filter_by(student_id=student_id, badge_id=badge.id).first()
    if not already_awarded:
        db.session.add(UserBadge(student_id=student_id, badge_id=badge.id))
        db.session.commit()

def evaluate_section_badges(student_id):
    completed_sections = SectionProgress.query.filter_by(student_id=student_id).count()

    if completed_sections >= 1:
        award_badge(student_id, "Section Starter")
    if completed_sections >= 5:
        award_badge(student_id, "Section Explorer")
    if completed_sections >= 10:
        award_badge(student_id, "Section Pro")

def evaluate_quiz_badges(student_id):
    passed_quizzes = QuizAttempt.query.filter_by(student_id=student_id, pass_status=True).count()

    if passed_quizzes >= 1:
        award_badge(student_id, "First Quiz Win")
    if passed_quizzes >= 3:
        award_badge(student_id, "Quiz Warrior")
    if passed_quizzes >= 5:
        award_badge(student_id, "Quiz Master")

def evaluate_assignment_badges(student_id):
    total_submissions = AssignmentSubmission.query.filter_by(student_id=student_id).count()

    if total_submissions >= 1:
        award_badge(student_id, "First Submission")
    if total_submissions >= 5:
        award_badge(student_id, "On a Roll")
    if total_submissions >= 10:
        award_badge(student_id, "Assignment Hero")
        

def evaluate_course_completion_badges(student_id, course_id):
    total_sections = LessonSection.query.join(Lesson).filter(Lesson.course_id == course_id).count()
    completed_sections = SectionProgress.query.join(LessonSection).join(Lesson).filter(
        Lesson.course_id == course_id,
        SectionProgress.student_id == student_id
    ).count()

    if total_sections > 0 and completed_sections == total_sections:
        award_badge(student_id, "Course Finisher")

def evaluate_timeliness_badges(student_id):
    submissions = AssignmentSubmission.query.filter_by(student_id=student_id).all()
    on_time_submissions = 0
    early_submissions = 0

    for s in submissions:
        assignment = Assignment.query.get(s.assignment_id)
        if assignment and assignment.due_date and s.created_at:
            if s.created_at <= assignment.due_date:
                on_time_submissions += 1
                if (assignment.due_date - s.created_at).total_seconds() >= 3600 * 24:
                    early_submissions += 1

    if early_submissions >= 1:
        award_badge(student_id, "Early Bird")
    if on_time_submissions >= 5:
        award_badge(student_id, "Always On Time")
