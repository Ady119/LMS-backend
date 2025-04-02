import os
from datetime import datetime
from utils.dropbox_service import get_temporary_download_link, delete_file_from_dropbox, upload_file
from werkzeug.utils import secure_filename, safe_join
from flask import Blueprint, jsonify, g, request, current_app, send_from_directory, abort, send_file, redirect
from sqlalchemy.orm import aliased, joinedload
from utils.badge_service import evaluate_all_badges
from urllib.parse import unquote
from utils.tokens import get_jwt_token, decode_jwt
from utils.utils import login_required
from datetime import date

from models.users import User, db
from models.section_progress import SectionProgress
from models.badges import Badge, UserBadge
from models.degrees import Degree
from models.courses import Course
from models.course_lecturers import CourseLecturer
from models.calendar_week import CalendarWeek
from models.academic_calendar import AcademicCalendar
from models.announcements import Announcement

from models.course_lessons import Lesson
from models.lesson_section import LessonSection
from models.assignment import Assignment
from models.quizzes import Quiz
from models.multiple_choice import MultipleChoiceQuestion
from models.short_quiz import ShortAnswerQuestion  
from models.quiz_attempts import QuizAttempt
from models.quiz_attempts_answers import QuizAttemptAnswer
from models.quiz_results import QuizResult
from models.enrolments import Enrolment
from models.assignment_submission import AssignmentSubmission

# Lecturers' blueprint
student_bp = Blueprint("student", __name__)

def get_upload_folder():
    return current_app.config.get["AvhievED-LMS"]


@student_bp.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", 
                  "http://127.0.0.1:5173", 
                  "http://localhost:4173", 
                  "lms-frontend-henna-sigma.vercel.app"]:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

#Fetch student's courses
@student_bp.route("/courses", methods=["GET"])
@login_required
def get_enrolled_courses():
    student_id = g.user.get("user_id")

    if not student_id:
        return jsonify({"error": "Invalid token"}), 401

    #Get degrees the student is enrolled in
    enrolled_degrees = db.session.query(Enrolment.degree_id).filter(
        Enrolment.student_id == student_id
    ).subquery()

    #Get courses linked to those degrees
    courses = db.session.query(
        Course.id, Course.title, Course.description
    ).filter(Course.degree_id.in_(enrolled_degrees)).all()

    courses_list = [{"id": c.id, "title": c.title, "description": c.description} for c in courses]

    return jsonify({"courses": courses_list})

#Fetch student's courses details
@student_bp.route("/courses/<int:course_id>", methods=["GET"])
@login_required
def get_course_details(course_id):
    student_id = g.user.get("user_id")

    if not student_id:
        return jsonify({"error": "Invalid token"}), 401

    #Check if the student is enrolled in a degree linked to this course
    course = db.session.query(Course).join(
        Enrolment, Course.degree_id == Enrolment.degree_id
    ).filter(
        Enrolment.student_id == student_id,
        Course.id == course_id
    ).first()

    if not course:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    return jsonify(course.to_dict()), 200

# Fetch a course' lessons
@student_bp.route("/courses/<int:course_id>/lessons", methods=["GET"])
@login_required
def get_student_lessons(course_id):
    student_id = g.user.get("user_id")

    if not student_id:
        return jsonify({"error": "Invalid token"}), 401

    # Check if student is directly enrolled in the course
    enrolled = db.session.query(Enrolment).join(
        Course, Enrolment.degree_id == Course.degree_id
    ).filter(
        Enrolment.student_id == student_id,
        Course.id == course_id
    ).first()

    if not enrolled:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    #  Get lessons for the course
    lessons = db.session.query(Lesson).filter_by(course_id=course_id).all()

    if not lessons:
        return jsonify({"message": "No lessons found for this course."}), 200

    return jsonify({"lessons": [lesson.to_dict() for lesson in lessons]}), 200

@student_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/content", methods=["GET"])
@login_required
def get_student_lesson_details(course_id, lesson_id):
    student_id = g.user.get("user_id")

    if not student_id:
        return jsonify({"error": "Invalid token"}), 401

    # Check if student is directly enrolled in the course
    enrolled = db.session.query(Enrolment).join(
        Course, Enrolment.degree_id == Course.degree_id
    ).filter(
        Enrolment.student_id == student_id,
        Course.id == course_id
    ).first()

    if not enrolled:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    # Fetch the lesson
    lesson = Lesson.query.filter_by(id=lesson_id, course_id=course_id).first()
    if not lesson:
        return jsonify({"error": "Lesson not found in this course"}), 404

    sections = (
        LessonSection.query
        .options(joinedload(LessonSection.calendar_week), joinedload(LessonSection.assignment), joinedload(LessonSection.quiz))
        .filter_by(lesson_id=lesson_id)
        .all()
    )

    lesson_data = {
        "id": lesson.id,
        "title": lesson.title if lesson.title else "Untitled Lesson",
        "description": lesson.description if lesson.description is not None else "",
        "sections": [
        {
        "id": section.id,
        "title": section.title,
        "content_type": section.content_type,
        "text_content": section.text_content if section.content_type == "text" else "",
        "file_url": section.file_url if section.content_type == "file" else None,
        "assignment": (
            {
                **section.assignment.to_dict(),
                "submissions": [
                    s.to_dict() for s in AssignmentSubmission.query.filter_by(
                        assignment_id=section.assignment.id,
                        student_id=student_id
                    ).all()
                ]
            }
            if section.assignment else None
        ),
        "quiz": section.quiz.to_dict() if section.quiz else None,
        "calendar_week_id": section.calendar_week_id,
        "calendar_week_label": section.calendar_week.label if section.calendar_week else None,
        "is_current_week": section.is_current_week,
    }
    for section in sections
    ],
    }

    return jsonify(lesson_data), 200


#download endpoin
@student_bp.route("/download/courses/<int:course_id>/lessons/<int:lesson_id>/<path:filename>")
@login_required
def download_student_file(course_id, lesson_id, filename):
    """Generate a Dropbox temporary link for students to download lesson files."""

    if not hasattr(g, "user"):
        return jsonify({"error": "Unauthorized"}), 401

    student_id = g.user.get("user_id")
    print(f"Student ID: {student_id}")

    # Check if student is enrolled in the course
    enrolled = db.session.query(Enrolment).join(
        Course, Enrolment.degree_id == Course.degree_id
    ).filter(
        Enrolment.student_id == student_id,
        Course.id == course_id
    ).first()

    if not enrolled:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    dropbox_folder = f"course_{course_id}/lesson_{lesson_id}"

    try:
        # Get Dropbox file link
        file_url = get_temporary_download_link(filename, folder=dropbox_folder)

        if not file_url:
            print(f"ERROR: File not found in Dropbox: {filename}")
            return jsonify({"error": "File not found"}), 404

        print(f" File found: {file_url}")
        return jsonify({"message": "File available for download", "file_url": file_url})

    except Exception as e:
        print(f" ERROR retrieving file from Dropbox: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


#                                                         QUIZZES 
#_____________________________________________________________________________________________________________
#Fetch quizz details
@student_bp.route("/quiz/<int:quiz_id>/details", methods=["GET"])
@login_required
def get_quiz_details(quiz_id):
    student_id = g.user.get("user_id")

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    # Fetch total questions
    short_answer_count = ShortAnswerQuestion.query.filter_by(quiz_id=quiz_id).count()
    multiple_choice_count = MultipleChoiceQuestion.query.filter_by(quiz_id=quiz_id).count()
    total_questions = short_answer_count + multiple_choice_count

    # Fetch previous attempts count
    existing_attempts = QuizAttempt.query.filter_by(student_id=student_id, quiz_id=quiz_id).count()
    attempts_left = max(0, quiz.max_attempts - existing_attempts)

    # Fetch latest attempt (if exists)
    latest_attempt = (
        QuizAttempt.query
        .filter_by(student_id=student_id, quiz_id=quiz_id)
        .order_by(QuizAttempt.completed_at.desc())
        .first()
    )
    attempt_id = latest_attempt.id if latest_attempt else None 

    return jsonify({
        "quiz_id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "max_attempts": quiz.max_attempts,
        "attempts_left": attempts_left,
        "time_limit": quiz.time_limit,
        "passing_score": quiz.passing_score,
        "total_questions": total_questions,
        "deadline": quiz.deadline.isoformat() if quiz.deadline else None,
        "attempt_id": attempt_id, 
        "multiple_choice_questions": [{"id": q.id, "question_text": q.question_text, "options": q.options} for q in quiz.multiple_choice_questions],
        "short_answer_questions": [{"id": q.id, "question_text": q.question_text} for q in quiz.short_answer_questions],
    }), 200


# Start a Quiz Attempt
@student_bp.route("/quiz/<int:quiz_id>/start", methods=["GET"])
@login_required
def start_quiz(quiz_id):
    """Fetch quiz details before starting, but do NOT create an attempt."""
    student_id = g.user.get("user_id")

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    # Fetch total questions
    short_answer_count = ShortAnswerQuestion.query.filter_by(quiz_id=quiz_id).count()
    multiple_choice_count = MultipleChoiceQuestion.query.filter_by(quiz_id=quiz_id).count()
    total_questions = short_answer_count + multiple_choice_count

    # Fetch previous attempts count
    existing_attempts = QuizAttempt.query.filter_by(student_id=student_id, quiz_id=quiz_id).count()
    attempts_left = max(0, quiz.max_attempts - existing_attempts)

    return jsonify({
        "quiz_id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "max_attempts": quiz.max_attempts,
        "attempts_left": attempts_left,
        "time_limit": quiz.time_limit,
        "passing_score": quiz.passing_score,
        "total_questions": total_questions,
        "deadline": quiz.deadline.isoformat() if quiz.deadline else None,
    }), 200


@student_bp.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    """Grades the quiz and provides feedback to students."""
    data = request.get_json()
    student_id = g.user.get("user_id")
    answers = data.get("answers", {})

    print(f" Received Answers from Student {student_id}: {answers}")  
    if not answers:
        print("ERROR: No answers received in the request!")

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    # Fetch previous attempts count
    existing_attempts = QuizAttempt.query.filter_by(student_id=student_id, quiz_id=quiz_id).count()
    if existing_attempts >= quiz.max_attempts:
        return jsonify({"error": "No attempts left"}), 403

    attempt = QuizAttempt(
        student_id=student_id,
        quiz_id=quiz_id,
        attempts_used=existing_attempts + 1,
        completed_at=datetime.utcnow(),
    )
    db.session.add(attempt)
    db.session.flush()  

    score = 0
    total_questions = len(quiz.multiple_choice_questions) + len(quiz.short_answer_questions)
    needs_review = False
    feedback = []

    # Grade Multiple Choice
    for question in quiz.multiple_choice_questions:
        user_answer = answers.get(f"mcq-{question.id}", "").strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        is_correct = user_answer == correct_answer

        print(f" Question {question.id} | Submitted: '{user_answer}' | Correct: '{correct_answer}' | Matched: {is_correct}")

        feedback.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "submitted_answer": user_answer or "No Answer",
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

        if is_correct:
            score += 1

    # Grade Short Answer
    for question in quiz.short_answer_questions:
        user_answer = answers.get(f"short-{question.id}", "").strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        is_correct = user_answer == correct_answer

        print(f"Question {question.id} | Submitted: '{user_answer}' | Correct: '{correct_answer}' | Matched: {is_correct}")

        feedback.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "submitted_answer": user_answer or "No Answer",
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

        if is_correct:
            score += 1
        else:
            needs_review = True

    percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0
    passed = percentage_score >= quiz.passing_score

    # Store Attempt Data
    attempt.score = percentage_score
    attempt.pass_status = passed
    attempt.needs_review = needs_review
    attempt.answers_temp = feedback
    
    # auto mark section complete 
    section = LessonSection.query.filter_by(quiz_id=quiz_id).first()
    if section and section.is_active:
        existing_progress = SectionProgress.query.filter_by(
            student_id=student_id,
            section_id=section.id
        ).first()
        if not existing_progress:
            db.session.add(SectionProgress(student_id=student_id, section_id=section.id))
            db.session.commit()
            new_badges = evaluate_all_badges(student_id, perfect_quiz_score=(percentage_score == 100))
        
    return jsonify({
        "score": percentage_score,
        "passed": passed,
        "needs_review": needs_review,
        "total_questions": total_questions,
        "attempts_used": attempt.attempts_used,
        "attempts_left": max(0, quiz.max_attempts - attempt.attempts_used),
        "feedback": feedback,
        "new_badges": new_badges
    }), 200


#Get Quiz Results
@student_bp.route("/quiz/<int:quiz_id>/results", methods=["GET"])
@login_required
def get_quiz_results(quiz_id):
    student_id = g.user.get("user_id")

    # Get the latest completed attempt
    attempt = QuizAttempt.query.filter_by(
        student_id=student_id, quiz_id=quiz_id
    ).order_by(QuizAttempt.completed_at.desc()).first()

    if not attempt:
        print(" No attempts found for this quiz!")
        return jsonify({"error": "No attempts found"}), 404

    # Ensure feedback is always a valid list
    feedback = attempt.answers_temp if attempt.answers_temp else []

    response_data = {
        "score": attempt.score,
        "pass_status": attempt.pass_status,
        "needs_review": attempt.needs_review,
        "attempts_used": attempt.attempts_used,
        "attempts_left": max(0, attempt.quiz.max_attempts - attempt.attempts_used),
        "feedback": feedback
    }

    return jsonify(response_data), 200


#Auto-Submit Quiz on Timeout
@student_bp.route("/quiz/<int:quiz_id>/auto-submit", methods=["POST"])
@login_required
def auto_submit_quiz(quiz_id):
    """Automatically submit the quiz if the student loses connection or time expires."""
    data = request.get_json()
    student_id = g.user.get("user_id")
    answers = data.get("answers", {})

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    existing_attempts = QuizAttempt.query.filter_by(student_id=student_id, quiz_id=quiz_id).count()
    if existing_attempts >= quiz.max_attempts:
        return jsonify({"error": "No attempts left"}), 403

    attempt = QuizAttempt(
        student_id=student_id,
        quiz_id=quiz_id,
        attempts_used=existing_attempts + 1,
        completed_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.flush()

    score = 0
    total_questions = len(quiz.multiple_choice_questions) + len(quiz.short_answer_questions)
    feedback = []
    needs_review = False

    # Grade Multiple Choice
    for question in quiz.multiple_choice_questions:
        user_answer = answers.get(str(question.id), "").strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1
        feedback.append({
            "question_id": question.id,
            "submitted_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    # Grade Short Answer
    for question in quiz.short_answer_questions:
        user_answer = answers.get(str(question.id), "").strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1
        else:
            needs_review = True
        feedback.append({
            "question_id": question.id,
            "submitted_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0
    passed = percentage_score >= quiz.passing_score

    attempt.score = percentage_score
    attempt.pass_status = passed
    attempt.needs_review = needs_review
    attempt.answers_temp = feedback

    db.session.commit()

    return jsonify({
        "message": "Quiz auto-submitted due to timeout.",
        "score": percentage_score,
        "passed": passed,
        "needs_review": needs_review
    }), 200


@student_bp.route("/quizzes/all", methods=["GET"])
@login_required
def get_available_quizzes():
    """Fetch all quizzes grouped by course, lesson, and section."""
    student_id = g.user.get("user_id")

    # Fetch quizzes based on lesson sections
    quizzes = (
        db.session.query(Quiz, Course, Lesson, LessonSection)
        .join(LessonSection, Quiz.id == LessonSection.quiz_id)
        .join(Lesson, LessonSection.lesson_id == Lesson.id)
        .join(Course, Lesson.course_id == Course.id)
        .all()
    )

    quiz_data = {}
    for quiz, course, lesson, section in quizzes:
        if course.id not in quiz_data:
            quiz_data[course.id] = {
                "course_id": course.id,
                "course_name": course.title,
                "lessons": {}
            }

        if lesson.id not in quiz_data[course.id]["lessons"]:
            quiz_data[course.id]["lessons"][lesson.id] = {
                "lesson_id": lesson.id,
                "lesson_title": lesson.title,
                "sections": {}
            }

        if section.id not in quiz_data[course.id]["lessons"][lesson.id]["sections"]:
            quiz_data[course.id]["lessons"][lesson.id]["sections"][section.id] = {
                "section_id": section.id,
                "section_title": section.title,
                "quizzes": []
            }

        quiz_data[course.id]["lessons"][lesson.id]["sections"][section.id]["quizzes"].append({
            "quiz_id": quiz.id,
            "title": quiz.title,
            "deadline": quiz.deadline,
            "max_attempts": quiz.max_attempts,
            "passing_score": quiz.passing_score
        })

    return jsonify(list(quiz_data.values())), 200

#Fetch All Assignments With Details
@student_bp.route("/assignments", methods=["GET"])
@login_required
def get_all_assignments():
    user_id = g.user.get("user_id")

    assignments = (
        db.session.query(Assignment)
        .join(LessonSection, LessonSection.assignment_id == Assignment.id)
        .filter(LessonSection.id.isnot(None))
        .options(
            joinedload(Assignment.sections)
            .joinedload(LessonSection.lesson)
            .joinedload(Lesson.course)
        )
        .distinct()
        .all()
    )

    assignment_list = []
    for assignment in assignments:
        for section in assignment.sections:
            if not section.lesson or not section.lesson.course:
                continue

            course = section.lesson.course
            lesson = section.lesson
            submissions = AssignmentSubmission.query.filter_by(
                assignment_id=assignment.id,
                student_id=user_id
            ).all()

            assignment_list.append({
                "id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "course_name": course.title,
                "lesson_title": lesson.title,
                "section_title": section.title,
                "submissions": [
                    {
                        "id": s.id,
                        "file_name": s.original_file_name or os.path.basename(s.file_url),
                        "file_url": s.file_url,
                        "submitted_at": s.submitted_at.isoformat()
                    } for s in submissions
                ]
            })

    return jsonify({"assignments": assignment_list}), 200

#submit assignment
@student_bp.route('/assignments/submit', methods=['POST'])
@login_required
def submit_assignment():
    user_id = g.user.get("user_id")

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    assignment_id = request.form.get('assignment_id')

    if not file:
        return jsonify({"error": "Invalid file"}), 400

    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Invalid assignment ID"}), 400

    lesson_section = LessonSection.query.filter_by(assignment_id=assignment.id).first()
    if not lesson_section:
        return jsonify({"error": "Assignment is not linked to a lesson"}), 400

    course_id = lesson_section.lesson.course_id
    lesson_id = lesson_section.lesson_id

    filename = secure_filename(file.filename)
    unique_filename = f"{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"

    dropbox_folder = f"assignments/course_{course_id}/lesson_{lesson_id}/assignment_{assignment.id}/student_{user_id}"

    # Check if an old submission
    old_submission = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=user_id).first()
    
    if old_submission and old_submission.file_url:
        try:
            delete_file_from_dropbox(old_submission.file_url)
            print(f"Old file deleted from Dropbox: {old_submission.file_url}")

        except Exception as e:
            print(f"Error deleting old file from Dropbox: {e}")

    try:
        # Upload new file to Dropbox
        public_url, _ = upload_file(file, unique_filename, folder=dropbox_folder)

        if not public_url:
            return jsonify({"error": "File upload to Dropbox failed"}), 500

        if old_submission:
            db.session.delete(old_submission)
            db.session.commit()

        # Add the new submission
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=user_id,
            file_url=public_url,
            original_file_name=file.filename,
        )
            
        db.session.add(submission)
        db.session.commit()
      
        # Auto mark section complete 
        already_completed = SectionProgress.query.filter_by(student_id=user_id, section_id=lesson_section.id).first()
        if not already_completed and lesson_section.is_active:
            db.session.add(SectionProgress(student_id=user_id, section_id=lesson_section.id))
            db.session.commit()
        
        # Evaluate badges based on the submission
        new_badges = evaluate_all_badges(user_id)
        
        return jsonify({
            "message": "Assignment submitted successfully!",
            "file_url": public_url,
            "new_badges": new_badges
        }), 200

    except Exception as e:
        print(f"Error uploading to Dropbox: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"File upload failed: {str(e)}"}), 500




#fetch assihnment details
@student_bp.route("/assignments/<int:assignment_id>", methods=["GET"])
@login_required
def get_assignment_details(assignment_id):
    assignment = Assignment.query.get(assignment_id)

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    return jsonify(assignment.to_dict()), 200

#fetch assignment submissin
@student_bp.route("/assignments/<int:assignment_id>/submissions", methods=["GET"])
@login_required
def get_assignment_submissions(assignment_id):
    user_id = g.user.get("user_id")

    submissions = AssignmentSubmission.query.filter_by(assignment_id=assignment_id, student_id=user_id).all()

    if not submissions:
        return jsonify({"message": "No submissions found"}), 200

    return jsonify([submission.to_dict() for submission in submissions]), 200

#delete assignment submission
@student_bp.route("/assignments/submissions/<int:submission_id>", methods=["DELETE"])
@login_required
def delete_assignment_submission(submission_id):
    user_id = g.user.get("user_id")

    submission = AssignmentSubmission.query.filter_by(id=submission_id, student_id=user_id).first()

    if not submission:
        return jsonify({"error": "Submission not found or unauthorized"}), 404

    if submission.file_url:
        try:
            delete_file_from_dropbox(submission.file_url) 
            print(f"File deleted from Dropbox: {submission.file_url}")

        except Exception as e:
            print(f" Error deleting file from Dropbox: {e}")
            return jsonify({"error": "Failed to delete file from Dropbox"}), 500

    db.session.delete(submission)
    db.session.commit()

    return jsonify({"message": "Submission deleted successfully"}), 200

#assignment file download
@student_bp.route('/download/courses/<int:course_id>/lessons/<int:lesson_id>/assignments/<int:assignment_id>/<string:file_name>')
@login_required
def download_assignment_file(course_id, lesson_id, assignment_id, file_name):
    user_id = g.user.get("user_id")

    dropbox_path = f"assignments/course_{course_id}/lesson_{lesson_id}/assignment_{assignment_id}/student_{user_id}/{file_name}"
    file_url = get_temporary_download_link(dropbox_path)

    if not file_url:
        return jsonify({"error": "Unable to generate Dropbox download link"}), 500

    return redirect(file_url)

#Fetch lesson assignments
@student_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/assignments", methods=["GET"])
@login_required
def get_lesson_assignments(course_id, lesson_id):
    user_id = g.user.get("user_id")

    sections = LessonSection.query.filter_by(lesson_id=lesson_id).filter(LessonSection.assignment_id.isnot(None)).options(
        joinedload(LessonSection.assignment)
    ).all()

    assignment_list = []
    for section in sections:
        assignment = section.assignment
        if assignment:
            submissions = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=user_id).all()
            assignment_list.append({
                "id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "section_title": section.title,
                "submissions": [
                    {
                        "id": s.id,
                        "file_name": os.path.basename(s.file_url),
                        "submitted_at": s.submitted_at.isoformat()
                    } for s in submissions
                ]
            })

    return jsonify({"assignments": assignment_list}), 200


@student_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/quizzes", methods=["GET"])
@login_required
def get_lesson_quizzes(course_id, lesson_id):
    user_id = g.user.get("user_id")

    sections = LessonSection.query.filter_by(lesson_id=lesson_id).filter(LessonSection.quiz_id.isnot(None)).options(
        joinedload(LessonSection.quiz)
    ).all()

    quiz_list = []
    for section in sections:
        quiz = section.quiz
        if quiz:
            quiz_list.append({
                **quiz.to_dict(),
                "section_title": section.title
            })

    return jsonify({"quizzes": quiz_list}), 200

#Mark a section complete
@student_bp.route("/sections/<int:section_id>/complete", methods=["POST"])
@login_required
def mark_section_complete(section_id):
    user_id = g.user.get("user_id")
    section = LessonSection.query.get(section_id)

    if not section or not section.is_active:
        return jsonify({"error": "Section is not available."}), 403

    existing = SectionProgress.query.filter_by(student_id=user_id, section_id=section_id).first()
    if existing:
        return jsonify({"message": "Already marked as completed.", "new_badges": []}), 200

    progress = SectionProgress(
        student_id=user_id,
        section_id=section_id,
        completed_at=datetime.utcnow()
    )
    db.session.add(progress)
    db.session.commit()
    new_badges = evaluate_all_badges(user_id)

    return jsonify({
        "message": "Section marked as completed.",
        "new_badges": new_badges
    }), 201

#Fetch compleded sections
@student_bp.route("/sections/completed", methods=["GET"])
@login_required
def get_completed_sections():
    user_id = g.user.get("user_id")
    progress = SectionProgress.query.filter_by(student_id=user_id).all()
    completed_ids = [p.section_id for p in progress]
    return jsonify({"completed_sections": completed_ids})

#Student dshboard stats
@student_bp.route("/dashboard", methods=["GET"])
@login_required
def get_student_dashboard():
    student_id = g.user.get("user_id")
    if not student_id:
        return jsonify({"error": "User not authenticated"}), 403

    from models import (
        Enrolment, Course, Lesson, LessonSection, SectionProgress, Degree,
        QuizAttempt, AssignmentSubmission, CourseLecturer, User
    )

    # Get enrolled degrees
    enrolled_degrees = (
        db.session.query(Degree)
        .join(Enrolment, Enrolment.degree_id == Degree.id)
        .filter(Enrolment.student_id == student_id)
        .all()
    )

    # Get courses
    enrolled_courses = (
        db.session.query(Course)
        .join(Degree, Course.degree_id == Degree.id)
        .filter(Course.degree_id.in_([d.id for d in enrolled_degrees]))
        .distinct()
        .all()
    )
    total_badges_earned = UserBadge.query.filter_by(student_id=student_id).count()
    total_courses = len(enrolled_courses)
    total_quizzes_attempted = db.session.query(QuizAttempt).filter_by(student_id=student_id).count()
    total_assignments_submitted = db.session.query(AssignmentSubmission).filter_by(student_id=student_id).count()

    course_stats = []
    for course in enrolled_courses:
        lecturer = (
            db.session.query(User.full_name)
            .join(CourseLecturer, CourseLecturer.lecturer_id == User.id)
            .filter(CourseLecturer.course_id == course.id)
            .first()
        )
        lecturer_name = lecturer[0] if lecturer else "To be confirmed."

        section_ids = (
            db.session.query(LessonSection.id)
            .join(Lesson, Lesson.id == LessonSection.lesson_id)
            .filter(Lesson.course_id == course.id)
            .all()
        )
        section_ids = [s.id for s in section_ids]
        total_sections = len(section_ids)

        completed = (
            db.session.query(SectionProgress)
            .filter(
                SectionProgress.student_id == student_id,
                SectionProgress.section_id.in_(section_ids)
            ).count()
        )

        progress = (completed / total_sections * 100) if total_sections else 0

        course_stats.append({
            "course_id": course.id,
            "course_title": course.title,
            "degree_name": course.degree.name if course.degree else "N/A",
            "lecturer_name": lecturer_name,
            "progress": round(progress, 2)
        })

    return jsonify({
        "total_courses": total_courses,
        "total_quizzes_attempted": total_quizzes_attempted,
        "total_assignments_submitted": total_assignments_submitted,
        "course_stats": course_stats,
        "total_badges_earned": total_badges_earned
    }), 200

#Fetch user badges
@student_bp.route("/badges", methods=["GET"])
@login_required
def get_user_badges():
    student_id = g.user.get("user_id")
    
    user_badges = (
        UserBadge.query
        .filter_by(student_id=student_id)
        .join(Badge)
        .all()
    )

    badge_data = [
        {
            "name": ub.badge.name,
            "description": ub.badge.description,
            "icon_url": ub.badge.icon_url,
            "awarded_at": ub.awarded_at.isoformat()
        }
        for ub in user_badges
    ]

    return jsonify(badge_data), 200

#student calendar
@student_bp.route("/calendar", methods=["GET"])
@login_required
def get_student_calendar():
    student_id = g.user["user_id"]

    # Get student's degree and courses
    degree_ids = db.session.query(Enrolment.degree_id).filter_by(student_id=student_id).subquery()
    course_ids = db.session.query(Course.id).filter(Course.degree_id.in_(degree_ids)).subquery()

    # Get lessons and sections
    lesson_ids = db.session.query(Lesson.id).filter(Lesson.course_id.in_(course_ids)).subquery()
    sections = (
        db.session.query(LessonSection)
        .filter(LessonSection.lesson_id.in_(lesson_ids))
        .filter(LessonSection.calendar_week_id.isnot(None))
        .join(CalendarWeek)
        .all()
    )

    events = []
    for section in sections:
        week = section.calendar_week
        course_title = section.lesson.course.title if section.lesson and section.lesson.course else ""
        events.append({
            "id": section.id,
            "title": f"{section.title} ({section.content_type})",
            "start": week.start_date.isoformat(),
            "end": week.end_date.isoformat(),
            "type": section.content_type,
            "course_title": course_title,
            "section_id": section.id
        })

    return jsonify(events), 200

#student profile
@student_bp.route("/profile", methods=["GET"])
@login_required
def get_student_profile():
    student_id = g.user["user_id"]

    user = User.query.get(student_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    enrolment = Enrolment.query.filter_by(student_id=student_id).first()
    degree = Degree.query.get(enrolment.degree_id) if enrolment else None
    calendar = AcademicCalendar.query.get(degree.calendar_id) if degree and degree.calendar_id else None

    # Course progress summary
    courses = Course.query.filter_by(degree_id=degree.id).all() if degree else []
    course_stats = []
    for course in courses:
        section_ids = (
            db.session.query(LessonSection.id)
            .join(Lesson, Lesson.id == LessonSection.lesson_id)
            .filter(Lesson.course_id == course.id)
            .all()
        )
        section_ids = [s.id for s in section_ids]
        total_sections = len(section_ids)
        completed = db.session.query(SectionProgress).filter(
            SectionProgress.student_id == student_id,
            SectionProgress.section_id.in_(section_ids)
        ).count()
        progress = (completed / total_sections * 100) if total_sections else 0
        course_stats.append({
            "course_id": course.id,
            "course_title": course.title,
            "progress": round(progress, 2)
        })

    # Badges earned
    badges = (
        db.session.query(UserBadge, Badge)
        .join(Badge, Badge.id == UserBadge.badge_id)
        .filter(UserBadge.student_id == student_id)
        .order_by(UserBadge.awarded_at.desc())
        .all()
    )

    badge_list = [
        {
            "id": b.Badge.id,
            "name": b.Badge.name,
            "description": b.Badge.description,
            "icon_url": b.Badge.icon_url,
            "awarded_at": b.UserBadge.awarded_at.isoformat()
        } for b in badges
    ]

    return jsonify({
        "user": {
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "institution": user.institution.name if user.institution else None,
            "date_joined": user.date_created.isoformat(),
        },
        "degree": {
            "name": degree.name if degree else None,
            "calendar_year": calendar.name if calendar else None,
            "start_date": calendar.start_date.isoformat() if calendar else None,
            "end_date": calendar.end_date.isoformat() if calendar else None,
        },
        "badges": badge_list,
        "courses": course_stats
    }), 200

@student_bp.route("/activities-today", methods=["GET"])
@login_required
def get_student_activities_today():
    student_id = g.user["user_id"]

    # Get course IDs from enrolled degrees
    degree_ids = db.session.query(Enrolment.degree_id).filter_by(student_id=student_id).subquery()
    course_ids = db.session.query(Course.id).filter(Course.degree_id.in_(degree_ids)).subquery()

    # Get sections scheduled present day
    lesson_ids = db.session.query(Lesson.id).filter(Lesson.course_id.in_(course_ids)).subquery()

    today = date.today()
    sections = (
        db.session.query(LessonSection)
        .filter(LessonSection.lesson_id.in_(lesson_ids))
        .join(CalendarWeek, LessonSection.calendar_week_id == CalendarWeek.id)
        .filter(CalendarWeek.start_date <= today, CalendarWeek.end_date >= today)
        .all()
    )

    events = [
        {
            "id": s.id,
            "title": s.title,
            "content_type": s.content_type,
            "course_title": s.lesson.course.title if s.lesson and s.lesson.course else "",
        } for s in sections
    ]

    return jsonify(events), 200
#student recent activity
@student_bp.route("/recent-activity", methods=["GET"])
@login_required
def get_student_recent_activity():
    student_id = g.user["user_id"]
    recent = []

    # Badges earned
    badge_entries = (
        db.session.query(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.student_id == student_id)
        .order_by(UserBadge.awarded_at.desc())
        .limit(3)
        .all()
    )
    for entry, badge in badge_entries:
        recent.append({
            "type": "badge",
            "message": f"Earned badge: {badge.name}",
            "timestamp": entry.awarded_at.isoformat()
        })

    # Quiz attempts
    quiz_attempts = (
        db.session.query(QuizAttempt)
        .filter_by(student_id=student_id)
        .order_by(QuizAttempt.completed_at.desc())
        .limit(3)
        .all()
    )
    for attempt in quiz_attempts:
        recent.append({
            "type": "quiz",
            "message": f"Completed a quiz with score {attempt.score:.0f}%",
            "timestamp": attempt.completed_at.isoformat() if attempt.completed_at else datetime.utcnow().isoformat()
        })

    # Assignment submissions
    submissions = (
        db.session.query(AssignmentSubmission)
        .filter_by(student_id=student_id)
        .order_by(AssignmentSubmission.submitted_at.desc())
        .limit(3)
        .all()
    )
    for sub in submissions:
        recent.append({
            "type": "assignment",
            "message": "Submitted an assignment",
            "timestamp": sub.submitted_at.isoformat()
        })

    # Section completions
    progress = (
        db.session.query(SectionProgress, LessonSection)
        .join(LessonSection, SectionProgress.section_id == LessonSection.id)
        .filter(SectionProgress.student_id == student_id)
        .order_by(SectionProgress.completed_at.desc())
        .limit(3)
        .all()
    )
    for p, section in progress:
        recent.append({
            "type": "section",
            "message": f"Completed: {section.title}",
            "timestamp": p.completed_at.isoformat()
        })

    recent.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify(recent[:6]), 200

#student all announcements
@student_bp.route("/announcements", methods=["GET"])
@login_required
def get_student_announcements():
    user_id = g.user.get("user_id")

    enrolled_course_ids = db.session.query(Enrolment.course_id).filter_by(student_id=user_id).subquery()

    # announcements for those courses
    announcements = (
        db.session.query(Announcement)
        .filter(Announcement.course_id.in_(enrolled_course_ids))
        .order_by(Announcement.created_at.desc())
        .all()
    )

    result = []
    for a in announcements:
        result.append({
            "id": a.id,
            "title": a.title,
            "message": a.message[:150] + "..." if len(a.message) > 150 else a.message,
            "course_id": a.course.id,
            "course_title": a.course.title,
            "created_at": a.created_at.isoformat()
        })

    return jsonify(result), 200

