import os
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from werkzeug.utils import secure_filename, safe_join
from flask import Blueprint, jsonify, g, request, current_app, send_from_directory, abort, send_file
from urllib.parse import unquote
from utils.tokens import get_jwt_token, decode_jwt
from utils.utils import login_required
from models.users import User, db
from models.courses import Course
from models.course_lessons import Lesson
from models.lesson_section import LessonSection
from models.quizzes import Quiz
from models.multiple_choice import MultipleChoiceQuestion
from models.short_quiz import ShortAnswerQuestion  
from models.quiz_attempts import QuizAttempt
from models.quiz_attempts_answers import QuizAttemptAnswer
from models.quiz_results import QuizResult
from models.enrolments import Enrolment
from models.assignment import Assignment

from models.assignment_submission import AssignmentSubmission
from sqlalchemy.orm import aliased, joinedload

# Lecturers' blueprint
student_bp = Blueprint("student", __name__)

def get_upload_folder():
    return current_app.config["UPLOAD_FOLDER"]


@student_bp.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"]:
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
def get_student_lesson_sections(course_id, lesson_id):
    student_id = g.user.get("user_id")

    if not student_id:
        return jsonify({"error": "Invalid token"}), 401

    # Ensure student is enrolled in the course
    enrolled = db.session.query(Enrolment).join(
        Course, Enrolment.degree_id == Course.degree_id
    ).filter(
        Enrolment.student_id == student_id,
        Course.id == course_id
    ).first()

    if not enrolled:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    sections = db.session.query(LessonSection).filter_by(lesson_id=lesson_id).all()

    lesson_data = {
        "lesson_id": lesson_id,
        "sections": []
    }

    for section in sections:
        section_data = {
            "id": section.id,
            "title": section.title,
            "content_type": section.content_type,
            "text_content": section.text_content if section.content_type == "text" else "",
            "file_url": section.file_url if section.content_type == "file" else None,
        }

        # Fetch quiz if exists
        if section.quiz_id:
            quiz = db.session.query(Quiz).filter_by(id=section.quiz_id).first()
            if quiz:
                section_data["quiz"] = {
                    "id": quiz.id,
                    "title": quiz.title,
                    "deadline": quiz.deadline,
                    "passing_score": quiz.passing_score,
                    "total_questions": quiz.total_questions, 
                    "time_limit":quiz.time_limit 
                }

        #  Fetch assignment if exists
        if section.assignment_id:
            assignment = db.session.query(Assignment).filter_by(id=section.assignment_id).first()
            if assignment:
                section_data["assignment"] = {
                    "id": assignment.id,
                    "title": assignment.title,
                    "description": assignment.description,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None
                }

        lesson_data["sections"].append(section_data)

    return jsonify(lesson_data), 200



@student_bp.route("/download/courses/<int:course_id>/lessons/<int:lesson_id>/<path:filename>")
@login_required
def download_student_file(course_id, lesson_id, filename):
    """Serve a file for download only if the student is enrolled."""
    
    #  Ensure g.user exists
    if not hasattr(g, "user"):
        return jsonify({"error": "Unauthorized"}), 401

    student_id = g.user.get("user_id")
    print(f"🔍 Student ID: {student_id}")

    #  Ensure student is enrolled in the course
    enrolled = db.session.query(Enrolment).join(
        Course, Enrolment.degree_id == Course.degree_id
    ).filter(
        Enrolment.student_id == student_id,
        Course.id == course_id
    ).first()

    if not enrolled:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    upload_folder = get_upload_folder()
    file_directory = os.path.abspath(os.path.join(upload_folder, f"course/{course_id}/lesson/{lesson_id}"))
    file_path = os.path.abspath(os.path.join(file_directory, filename))

    print(f"Flask is trying to serve file from: {file_path}")

    # Debugging: Check if the directory exists
    if os.path.exists(file_directory):
        print(f"Files inside: {os.listdir(file_directory)}")
    else:
        print(f"ERROR: Directory {file_directory} does not exist!")

    # Check if the requested file exists
    if os.path.exists(file_path):
        print(f"FILE FOUND! Downloading: {file_path}")
        return send_file(file_path, as_attachment=True)
    else:
        print(f"ERROR: File NOT found at {file_path}")

        lowercase_files = [f.lower() for f in os.listdir(file_directory)]
        if filename.lower() in lowercase_files:
            print("WARNING: Filename case mismatch! Try renaming the file.")

        abort(404, description=f"File not found at {file_path}")



#                                                         QUIZZES 
#_____________________________________________________________________________________________________________
#Fetch quizz details
@student_bp.route("/quiz/<int:quiz_id>/details", methods=["GET"])
@login_required
def get_quiz_details(quiz_id):
    """Fetch quiz details including total questions, attempts left, and latest attempt ID."""
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
        user_answer = answers.get(str(question.id), "").strip().lower()
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
        user_answer = answers.get(str(question.id), "").strip().lower()
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

    db.session.commit()

    return jsonify({
        "score": percentage_score,
        "passed": passed,
        "needs_review": needs_review,
        "total_questions": total_questions,
        "attempts_used": attempt.attempts_used,
        "attempts_left": max(0, quiz.max_attempts - attempt.attempts_used),
        "feedback": feedback
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
    """Automatically submit the quiz if the student loses connection or time expires"""
    data = request.get_json()
    student_id = g.user.get("user_id")
    answers = data.get("answers", {})

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    # Check if they already submitted
    existing_attempts = QuizAttempt.query.filter_by(student_id=student_id, quiz_id=quiz_id).count()
    if existing_attempts >= quiz.max_attempts:
        return jsonify({"error": "No attempts left"}), 403

    # Create attempt NOW
    attempt = QuizAttempt(
        student_id=student_id,
        quiz_id=quiz_id,
        attempts_used=existing_attempts + 1,
        completed_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.flush()

    unanswered_questions = len(quiz.multiple_choice_questions) + len(quiz.short_answer_questions) - len(answers)
    score = (len(answers) / (unanswered_questions + len(answers))) * 100 if unanswered_questions else 0
    passed = score >= quiz.passing_score

    attempt.score = score
    attempt.pass_status = passed
    attempt.needs_review = False

    db.session.commit()

    return jsonify({
        "message": "Quiz auto-submitted due to timeout",
        "score": score,
        "passed": passed,
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

    # Fetch all assignments with related Course, Lesson, and Section
    assignments = db.session.query(Assignment).options(
        joinedload(Assignment.sections)
    ).all()

    assignment_list = []
    for assignment in assignments:
        section = assignment.sections[0] if assignment.sections else None
        lesson = section.lesson if section else None
        course = lesson.course if lesson else None

        assignment_list.append({
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "course_name": course.title if course else "Unknown Course",
            "lesson_title": lesson.title if lesson else "Unknown Lesson",
            "section_title": section.title if section else "Unknown Section",
            "submissions": [
                {
                    "id": submission.id,
                    "file_name": os.path.basename(submission.file_url),
                    "submitted_at": submission.submitted_at.isoformat()
                }
                for submission in AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=user_id).all()
            ],
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

    # Validate assignment ID
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Invalid assignment ID"}), 400

    # Fetch course_id and lesson_id from LessonSection
    lesson_section = LessonSection.query.filter_by(assignment_id=assignment.id).first()
    if not lesson_section:
        return jsonify({"error": "Assignment is not linked to a lesson"}), 400

    course_id = lesson_section.lesson.course_id
    lesson_id = lesson_section.lesson_id

    upload_root = get_upload_folder()

    # structured folder inside "uploads/"
    relative_folder_path = os.path.join(
        "assignments", 
        f"course_{course_id}", 
        f"lesson_{lesson_id}", 
        f"assignment_{assignment.id}", 
        f"student_{user_id}"
    )
    
    absolute_folder_path = os.path.join(upload_root, relative_folder_path)
    os.makedirs(absolute_folder_path, exist_ok=True)

    # Check if an existing submission exists and delete the old file
    old_submission = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=user_id).first()
    if old_submission:
        old_file_path = os.path.join(upload_root, old_submission.file_url)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        db.session.delete(old_submission)
        db.session.commit()

    filename = secure_filename(file.filename)
    file_path = os.path.join(absolute_folder_path, filename)
    file.save(file_path)

    relative_file_path = os.path.join(relative_folder_path, filename)

    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=user_id,
        file_url=relative_file_path
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({"message": "Assignment submitted successfully!", "file_url": relative_file_path}), 201


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

    # Get all submissions for this student and assignment
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

    # Delete the file from the server
    file_path = os.path.join(get_upload_folder(), submission.file_url)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(submission)
    db.session.commit()

    return jsonify({"message": "Submission deleted successfully"}), 200

#assignment file download
@student_bp.route("/assignments/<int:assignment_id>/submissions/<int:submission_id>/download", methods=["GET"])
@login_required
def download_assignment_submission(assignment_id, submission_id):
    submission = AssignmentSubmission.query.filter_by(id=submission_id, assignment_id=assignment_id).first()
    
    if not submission:
        return jsonify({"error": "File not found"}), 404
    
    file_path = submission.file_url
    directory, filename = os.path.split(file_path)
    
    return send_from_directory(directory, filename, as_attachment=True)
