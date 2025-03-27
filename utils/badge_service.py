from models import db, Badge, UserBadge, SectionProgress, QuizAttempt
from sqlalchemy import func
from models.assignment import Assignment
from models.assignment_submission import AssignmentSubmission
from models.courses import Course
from models.course_lessons import Lesson
from models.lesson_section import LessonSection
from models.section_progress import SectionProgress
from datetime import datetime

def award_badge(student_id, badge_name):
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge:
        return None 

    already_awarded = UserBadge.query.filter_by(student_id=student_id, badge_id=badge.id).first()
    if not already_awarded:
        new_badge = UserBadge(student_id=student_id, badge_id=badge.id, awarded_at=datetime.utcnow())
        db.session.add(new_badge)
        db.session.flush()
        return {
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "icon_url": badge.icon_url
        }
    return None 

def evaluate_section_badges(student_id):
    badges = []
    completed_sections = SectionProgress.query.filter_by(student_id=student_id).count()

    if completed_sections >= 1:
        b = award_badge(student_id, "Section Starter")
        if b: badges.append(b)
    if completed_sections >= 5:
        b = award_badge(student_id, "Section Explorer")
        if b: badges.append(b)
    if completed_sections >= 10:
        b = award_badge(student_id, "Section Pro")
        if b: badges.append(b)
    return badges

def evaluate_quiz_badges(student_id, perfect_score=False):
    badges = []
    passed_quizzes = QuizAttempt.query.filter_by(student_id=student_id, pass_status=True).count()

    if passed_quizzes >= 1:
        b = award_badge(student_id, "First Quiz Win")
        if b: badges.append(b)
    if passed_quizzes >= 3:
        b = award_badge(student_id, "Quiz Warrior")
        if b: badges.append(b)
    if passed_quizzes >= 5:
        b = award_badge(student_id, "Quiz Master")
        if b: badges.append(b)

    if perfect_score:
        b = award_badge(student_id, "Perfect Quiz Score")
        if b: badges.append(b)

    return badges

def evaluate_assignment_badges(student_id):
    badges = []
    total_submissions = AssignmentSubmission.query.filter_by(student_id=student_id).count()

    if total_submissions >= 1:
        b = award_badge(student_id, "First Submission")
        if b: badges.append(b)
    if total_submissions >= 5:
        b = award_badge(student_id, "On a Roll")
        if b: badges.append(b)
    if total_submissions >= 10:
        b = award_badge(student_id, "Assignment Hero")
        if b: badges.append(b)
    return badges

def evaluate_course_completion_badges(student_id, course_id):
    badges = []
    total_sections = LessonSection.query.join(Lesson).filter(Lesson.course_id == course_id).count()
    completed_sections = SectionProgress.query.join(LessonSection).join(Lesson).filter(
        Lesson.course_id == course_id,
        SectionProgress.student_id == student_id
    ).count()

    if total_sections > 0 and completed_sections == total_sections:
        b = award_badge(student_id, "Course Finisher")
        if b: badges.append(b)
    return badges

def evaluate_timeliness_badges(student_id):
    badges = []
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
        b = award_badge(student_id, "Early Bird")
        if b: badges.append(b)
    if on_time_submissions >= 5:
        b = award_badge(student_id, "Always On Time")
        if b: badges.append(b)
    return badges

def evaluate_all_badges(student_id, course_id=None, perfect_quiz_score=False):
    new_badges = []

    new_badges += evaluate_section_badges(student_id)
    new_badges += evaluate_quiz_badges(student_id, perfect_score=perfect_quiz_score)
    new_badges += evaluate_assignment_badges(student_id)
    new_badges += evaluate_timeliness_badges(student_id)

    if course_id:
        new_badges += evaluate_course_completion_badges(student_id, course_id)

    return new_badges
