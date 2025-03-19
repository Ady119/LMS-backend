import os
from werkzeug.utils import secure_filename
import os
from werkzeug.utils import secure_filename, safe_join
from flask import Blueprint, jsonify, g, request, current_app, send_from_directory, abort
from urllib.parse import unquote
from utils.tokens import get_jwt_token, decode_jwt
from utils.utils import login_required
from models.users import User, db
from models.courses import Course
from models.course_lecturers import CourseLecturer
from models.course_lessons import Lesson
from models.lesson_section import LessonSection
from models.quizzes import Quiz
from models.multiple_choice import MultipleChoiceQuestion
from models.short_quiz import ShortAnswerQuestion  

from models.assignment import Assignment
from sqlalchemy.orm import aliased

# Lecturers' blueprint
lecturer_bp = Blueprint("lecturer", __name__)

def get_upload_folder():
    return current_app.config["UPLOAD_FOLDER"]

@lecturer_bp.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", 
                  "http://127.0.0.1:5173", 
                  "http://localhost:4173", 
                  "lms-frontend-henna-seven.vercel.app"]:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

#__________________________________________________________________________________________ * Courses *__________________________________________________

# fetch all courses
@lecturer_bp.route("/courses", methods=["GET"])
@login_required
def get_my_courses():
    lecturer_id = g.user.get("user_id")

    print(f"🔍 Lecturer ID: {lecturer_id}")  # ✅ Check if user ID is correct

    if not lecturer_id:
        return jsonify({"error": "Invalid token"}), 401

    courses = db.session.query(
        Course.id, Course.title, Course.description
    ).join(CourseLecturer, Course.id == CourseLecturer.course_id
    ).filter(CourseLecturer.lecturer_id == lecturer_id).all()

    print(f"🔍 Courses Found: {courses}")  # ✅ Debugging

    courses_list = [{"id": c.id, "title": c.title, "description": c.description} for c in courses]

    return jsonify({"courses": courses_list})


# Fetch course details
@lecturer_bp.route("/courses/<int:course_id>", methods=["GET"])
@login_required
def get_course_details(course_id):
    user_id = g.user.get("user_id")

    course = db.session.query(Course).join(CourseLecturer).filter(
        CourseLecturer.lecturer_id == user_id,
        Course.id == course_id
    ).first()

    if not course:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    return jsonify(course.to_dict()), 200

# Fetch a course' lessons
@lecturer_bp.route("/courses/<int:course_id>/lessons", methods=["GET"])
@login_required
def get_lessons(course_id):
    user_id = g.user.get("user_id")

    course = db.session.query(Course).join(CourseLecturer).filter(
        CourseLecturer.lecturer_id == user_id,
        Course.id == course_id
    ).first()

    if not course:
        return jsonify({"error": "Unauthorized or course not found"}), 403

    lessons = db.session.query(Lesson).filter_by(course_id=course_id).all()

    return jsonify({"lessons": [lesson.to_dict() for lesson in lessons]}), 200

#__________________________________________________________________________________________ * Lessons *__________________________________________________

#add/create a new  lesson to a course
@lecturer_bp.route("/courses/<int:course_id>/lessons", methods=["POST"])
@login_required
def add_lesson(course_id):
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    user_id = g.user.get("user_id")
    
    if not title:
        return jsonify({"error": "Title is required"}), 400

    #Check if the logged-in lecturer owns the course
    course = CourseLecturer.query.filter_by(course_id=course_id, lecturer_id=g.user.get("user_id")).first()
    if not course:
        return jsonify({"error": "You do not have permission to add lessons to this course"}), 403

    new_lesson = Lesson(course_id=course_id, title=title, description=description)
    db.session.add(new_lesson)
    db.session.commit()

    return jsonify({"message": "Lesson created successfully", "lesson": new_lesson.to_dict()}), 201

# Edit lesson
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>", methods=["PUT"])
@login_required
def edit_lesson(course_id, lesson_id):
    user_id = g.user.get("user_id")

    lesson = Lesson.query.filter_by(id=lesson_id, course_id=course_id).first()
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404

    # Check if the logged-in lecturer is assigned to the course
    lesson = Lesson.query.join(CourseLecturer, Lesson.course_id == CourseLecturer.course_id).filter(
        Lesson.id == lesson_id,
        Lesson.course_id == course_id,
        CourseLecturer.lecturer_id == user_id
    ).first()
    data = request.get_json()
    print("Received Data:", data)

    if not lesson:
        return jsonify({"error": "You do not have permission to edit this lesson"}), 403

    data = request.get_json()
    lesson.title = data.get("title", lesson.title)
    lesson.description = data.get("description") if data.get("description") is not None else lesson.description

    db.session.commit()

    return jsonify({"message": "Lesson updated successfully", "lesson": lesson.to_dict()})


# Delete a lesson
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>", methods=["DELETE"])
@login_required
def delete_lesson(course_id, lesson_id):
    user_id = g.user.get("user_id")

    lesson = Lesson.query.filter_by(id=lesson_id, course_id=course_id).first()
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404

    # Check if the logged-in lecturer is assigned to the course
    lesson = Lesson.query.join(CourseLecturer, Lesson.course_id == CourseLecturer.course_id).filter(
        Lesson.id == lesson_id,
        Lesson.course_id == course_id,
        CourseLecturer.lecturer_id == user_id
    ).first()

    if not lesson:
        return jsonify({"error": "You do not have permission to delete this lesson"}), 403

    # Delete lesson and commit
    db.session.delete(lesson)
    db.session.commit()

    return jsonify({"message": "Lesson deleted successfully"})


@lecturer_bp.route('/courses/<int:course_id>/lessons/<int:lesson_id>/sections/<int:section_id>', methods=['DELETE'])
@login_required
def delete_section(course_id, lesson_id, section_id):
    """Deletes a lesson section and removes any associated file."""
    
    section = LessonSection.query.filter_by(id=section_id, lesson_id=lesson_id).first()

    if not section:
        return jsonify({"error": "Section not found"}), 404

    upload_folder = get_upload_folder()

    if section.file_url:
        file_path = os.path.abspath(os.path.join(get_upload_folder(), section.file_url.replace("uploads/", "", 1)))
        
        if os.path.exists(file_path):
            print(f"Deleting file: {file_path}")
            os.remove(file_path)  # Remove file
        else:
            print(f"File not found for deletion: {file_path}")

    db.session.delete(section)
    db.session.commit()

    return jsonify({"message": "Section and associated file deleted successfully"})


# Fetch lesson details and its sectiosn
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/content", methods=["GET"])
@login_required
def get_lesson_details(course_id, lesson_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    lesson = Lesson.query.filter_by(id=lesson_id, course_id=course_id).first()
    if not lesson:
        return jsonify({"error": "Lesson not found in this course"}), 404

    sections = LessonSection.query.filter_by(lesson_id=lesson_id).all()

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
            }
            for section in sections
        ],
    }

    return jsonify(lesson_data), 200


#Fetch assignments
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/assignments", methods=["GET"])
@login_required
def get_available_assignments(course_id, lesson_id):
    assignments = Assignment.query.filter_by(lesson_id=lesson_id).all()
    return jsonify([assignment.to_dict() for assignment in assignments]), 200

def get_upload_folder():
    return current_app.config["UPLOAD_FOLDER"]

ALLOWED_EXTENSIONS = {"pdf", "jpg", "png", "mp4", "zip", "txt", "docx"}

# Check if the file extension is valid
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, course_id=None, lesson_id=None, is_assignment=False):
    """Securely saves uploaded files inside the correct directory based on type (assignment or lesson content)."""
    if not file or not allowed_file(file.filename):
        return None, "Invalid file type"

    upload_folder = get_upload_folder()

    if is_assignment:
        # Save under general assignments if it's an assignment
        save_folder = os.path.join(upload_folder, "assignments")
    else:
        # Save under course & lesson directory
        if not course_id or not lesson_id:
            return None, "Course ID and Lesson ID required for lesson content"
        save_folder = os.path.join(upload_folder, f"course/{course_id}/lesson/{lesson_id}")

    os.makedirs(save_folder, exist_ok=True)

    filename = secure_filename(file.filename.replace(" ", "_"))
    file_path = os.path.join(save_folder, filename)

    print(f"File should be saved to: {file_path}")

    file.save(file_path)

    if is_assignment:
        return f"uploads/assignments/{filename}", None
    return f"uploads/course/{course_id}/lesson/{lesson_id}/{filename}", None


#                          **Upload a New Section (Handles File Upload)**
# ------------------------------------------------------------------------------------------------
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/sections", methods=["POST"])
@login_required
def add_section(course_id, lesson_id):
    """Add a new section to a lesson, linking an existing assignment or quiz if provided."""

    title = request.form.get("title")
    content_type = request.form.get("content_type")
    text_content = request.form.get("text_content")
    file = request.files.get("file")
    assignment_id = request.form.get("assignment_id")
    quiz_id = request.form.get("quiz_id")

    if not title or not content_type:
        return jsonify({"error": "Title and content type are required"}), 400

    # Ensure only one type of linked content
    if assignment_id and quiz_id:
        return jsonify({"error": "Cannot assign both quiz and assignment to the same section"}), 400

    saved_file_path = None
    if file:
        saved_file_path, error = save_uploaded_file(file, course_id, lesson_id)
        if error:
            return jsonify({"error": error}), 400

    new_section = LessonSection(
        lesson_id=lesson_id,
        title=title,
        content_type=content_type,
        text_content=text_content,
        file_url=saved_file_path,
        assignment_id=assignment_id,
        quiz_id=quiz_id
    )

    db.session.add(new_section)
    db.session.commit()

    return jsonify({"message": "Section added successfully", "section": new_section.to_dict()}), 201


# ------------------------------------------------------------------------------------------------
# **Edit Existing Section**
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/sections/<int:section_id>", methods=["PUT"])
@login_required
def edit_section(course_id, lesson_id, section_id):
    """Handles updating an existing section, including replacing a file if a new one is uploaded."""

    section = LessonSection.query.filter_by(id=section_id, lesson_id=lesson_id).first()
    if not section:
        return jsonify({"error": "Section not found"}), 404

    data = request.form if request.form else request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    title = data.get("title", section.title)
    content_type = data.get("content_type", section.content_type)
    text_content = data.get("text_content", section.text_content)
    quiz_id = data.get("quiz_id", section.quiz_id)
    assignment_id = data.get("assignment_id", section.assignment_id)

    # Handle File Upload (If a new file is provided, delete the old one)
    file = request.files.get("file")
    file_url = section.file_url  # Keep existing file unless replaced

    upload_folder = get_upload_folder()

    if content_type == "file" and file:
        # Delete the old file if it exists
        if section.file_url:
            old_file_path = os.path.abspath(os.path.join(upload_folder, section.file_url.replace("uploads/", "", 1)))
            if os.path.exists(old_file_path):
                print(f"🗑️ Deleting old file: {old_file_path}")
                os.remove(old_file_path)

        file_url, error = save_uploaded_file(file, course_id, lesson_id)
        if error:
            return jsonify({"error": error}), 400

    section.title = title
    section.content_type = content_type

    if content_type == "quiz":
        section.quiz_id = quiz_id
        section.assignment_id = None
        section.file_url = None
        section.text_content = None
    elif content_type == "assignment":
        section.assignment_id = assignment_id
        section.quiz_id = None
        section.file_url = None
        section.text_content = None
    elif content_type == "file":
        section.file_url = file_url
        section.quiz_id = None
        section.assignment_id = None
        section.text_content = None
    elif content_type == "text":
        section.text_content = text_content
        section.quiz_id = None
        section.assignment_id = None
        section.file_url = None

    db.session.commit()
    return jsonify({"message": "Section updated successfully", "section": section.to_dict()}), 200



#                                       **Serve Uploaded Files**
# ------------------------------------------------------------------------------------------------
from flask import send_file

@lecturer_bp.route("/download/course/<int:course_id>/lesson/<int:lesson_id>/<path:filename>")
def download_file(course_id, lesson_id, filename):
    """Serve a file for download and print exact paths for debugging."""
    upload_folder = get_upload_folder()
    file_directory = os.path.abspath(os.path.join(upload_folder, f"course/{course_id}/lesson/{lesson_id}"))
    file_path = os.path.abspath(os.path.join(file_directory, filename))

    print(f"Flask is trying to serve file from: {file_path}")

    # List all files in the directory
    if os.path.exists(file_directory):
        print(f"Directory exists: {file_directory}")
        print(f"Files inside: {os.listdir(file_directory)}")
    else:
        print(f"ERROR: Directory {file_directory} does not exist!")

    if os.path.exists(file_path):
        print(f"FILE FOUND! Downloading: {file_path}")
        return send_file(file_path, as_attachment=True)
    else:
        print(f"ERROR: File NOT found at {file_path}")

        print(f" Files in directory: {os.listdir(file_directory)}")
        print(f" Expected filename: '{filename}'")
        
        # Check if the filename exists with different casing
        lowercase_files = [f.lower() for f in os.listdir(file_directory)]
        if filename.lower() in lowercase_files:
            print("WARNING: Filename case mismatch! Try renaming the file.")

        abort(404, description=f"File not found at {file_path}")

#Fetch All Quizzes
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes", methods=["GET"])
@login_required
def get_all_quizzes():
    quizzes = Quiz.query.all()
    return jsonify([quiz.to_dict() for quiz in quizzes]), 200

#Fetch one single quiz
@lecturer_bp.route("/quizzes/<int:quiz_id>", methods=["GET"])
@login_required
def get_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    
    return jsonify(quiz.to_dict()), 200

@lecturer_bp.route("/quizzes/<int:quiz_id>/view", methods=["GET"], endpoint="view_quiz_details")
@login_required
def get_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    short_answer_questions = ShortAnswerQuestion.query.filter_by(quiz_id=quiz_id).all()
    multiple_choice_questions = MultipleChoiceQuestion.query.filter_by(quiz_id=quiz_id).all()

    return jsonify({
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "max_attempts": quiz.max_attempts,
        "time_limit": quiz.time_limit,
        "randomize_questions": quiz.randomize_questions,
        "immediate_feedback": quiz.immediate_feedback,
        "passing_score": quiz.passing_score,
        "deadline": quiz.deadline.strftime("%Y-%m-%d") if quiz.deadline else None,
        "short_answer_questions": [q.to_dict() for q in short_answer_questions],
        "multiple_choice_questions": [q.to_dict() for q in multiple_choice_questions],
    }), 200


#CREATE a New Quiz
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/new", methods=["POST"])
@login_required
def create_quiz():
    data = request.json

    title = data.get("title")
    description = data.get("description")
    max_attempts = data.get("max_attempts", 3)
    time_limit = data.get("time_limit")
    randomize_questions = data.get("randomize_questions", False)
    immediate_feedback = data.get("immediate_feedback", False)
    passing_score = data.get("passing_score", 50)
    deadline = data.get("deadline")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    new_quiz = Quiz(
        title=title,
        description=description,
        max_attempts=max_attempts,
        time_limit=time_limit,
        randomize_questions=randomize_questions,
        immediate_feedback=immediate_feedback,
        passing_score=passing_score,
        deadline=deadline
    )

    db.session.add(new_quiz)
    db.session.commit()

    return jsonify({"message": "Quiz created successfully", "quiz": new_quiz.to_dict()}), 201


# EDIT a Quiz (Only Title & Description)
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/edit", methods=["PUT"])
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    data = request.json

    # Update only the provided fields
    quiz.title = data.get("title", quiz.title)
    quiz.description = data.get("description", quiz.description)
    quiz.max_attempts = data.get("max_attempts", quiz.max_attempts)
    quiz.time_limit = data.get("time_limit", quiz.time_limit)
    quiz.randomize_questions = data.get("randomize_questions", quiz.randomize_questions)
    quiz.immediate_feedback = data.get("immediate_feedback", quiz.immediate_feedback)
    quiz.passing_score = data.get("passing_score", quiz.passing_score)
    quiz.deadline = data.get("deadline", quiz.deadline)

    db.session.commit()

    return jsonify({"message": "Quiz updated successfully", "quiz": quiz.to_dict()}), 200


# DELETE a Quiz
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/delete", methods=["DELETE"])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    db.session.delete(quiz)
    db.session.commit()

    return jsonify({"message": "Quiz deleted successfully"}), 200


# GET Questions for a Quiz (Both Types)
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions", methods=["GET"])
@login_required
def get_questions(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    short_answer_questions = [
        {**q.to_dict(), "id": f"short-{q.id}"} for q in quiz.short_answer_questions
    ]
    multiple_choice_questions = [
        {**q.to_dict(), "id": f"multi-{q.id}"} for q in quiz.multiple_choice_questions
    ]

    return jsonify({
        "short_answer_questions": short_answer_questions,
        "multiple_choice_questions": multiple_choice_questions
    }), 200


#  CREATE a Short-Answer Question
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/short-answer/new", methods=["POST"])
@login_required
def add_short_answer_question(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    data = request.json
    question_text = data.get("question_text")
    correct_answer = data.get("correct_answer")

    if not question_text or correct_answer is None:
        return jsonify({"error": "Invalid question data"}), 400

    question = ShortAnswerQuestion (
        quiz_id=quiz_id,
        question_text=question_text,
        correct_answer=correct_answer
    )

    db.session.add(question)
    db.session.commit()

    return jsonify({"message": "Short-answer question added", "question": question.to_dict()}), 201

# CREATE a Multiple-Choice Question
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/multiple-choice/new", methods=["POST"])
@login_required
def add_multiple_choice_question(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    data = request.json
    question_text = data.get("question_text")
    options = data.get("options")
    correct_answer = data.get("correct_answer")

    if not question_text or not options or correct_answer is None:
        return jsonify({"error": "Invalid question data"}), 400

    if len(options) < 2:
        return jsonify({"error": "Multiple-choice questions need at least two options"}), 400

    question = MultipleChoiceQuestion(
        quiz_id=quiz_id,
        question_text=question_text,
        options=options,
        correct_answer=correct_answer
    )

    db.session.add(question)
    db.session.commit()

    return jsonify({"message": "Multiple-choice question added", "question": question.to_dict()}), 201

#Edit Short-Answer Question
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/short-answer/<int:question_id>/edit", methods=["PUT"])
@login_required
def edit_short_answer_question(quiz_id, question_id):
    """Edit an existing short-answer question"""
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    question = ShortAnswerQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first()
    if not question:
        return jsonify({"error": "Question not found"}), 404

    data = request.json
    question_text = data.get("question_text", question.question_text)
    correct_answer = data.get("correct_answer", question.correct_answer)

    if not question_text or not correct_answer:
        return jsonify({"error": "Invalid question data"}), 400

    question.question_text = question_text
    question.correct_answer = correct_answer

    db.session.commit()

    return jsonify({"message": "Short-answer question updated successfully", "question": question.to_dict()}), 200

#Edit multiple-choice Question
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/multiple-choice/<int:question_id>/edit", methods=["PUT"])
@login_required
def edit_multiple_choice_question(quiz_id, question_id):
    """Edit an existing multiple-choice question"""
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    question = MultipleChoiceQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first()
    if not question:
        return jsonify({"error": "Question not found"}), 404

    data = request.json
    question_text = data.get("question_text", question.question_text)
    options = data.get("options", question.options)
    correct_answer = data.get("correct_answer", question.correct_answer)

    if not question_text or not options or not correct_answer:
        return jsonify({"error": "Invalid question data"}), 400

    question.question_text = question_text
    question.options = options  # Should be a list of choices
    question.correct_answer = correct_answer

    db.session.commit()

    return jsonify({"message": "Multiple-choice question updated successfully", "question": question.to_dict()}), 200


# DELETE a Short-Answer Question
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/questions/short-answer/<int:question_id>/delete", methods=["DELETE"])
@login_required
def delete_short_answer_question(question_id):
    question = ShortAnswerQuestion  .query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    db.session.delete(question)
    db.session.commit()
    
    return jsonify({"message": "Short-answer question deleted"}), 200

# DELETE a Multiple-Choice Question
# --------------------------------------------------------------------------------
@lecturer_bp.route("/quizzes/questions/multiple-choice/<int:question_id>/delete", methods=["DELETE"])
@login_required
def delete_multiple_choice_question(question_id):
    question = MultipleChoiceQuestion.query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    db.session.delete(question)
    db.session.commit()
    
    return jsonify({"message": "Multiple-choice question deleted"}), 200


#                                            **ASSIGNMENTS**
#_________________________________________________________________________________________________

#Get all assignments created by a lecturer (across courses)
@lecturer_bp.route("/assignments", methods=["GET"], endpoint="get_assignments")
@login_required
def get_available_assignments():
    """Fetch all assignments that are available for selection."""
    assignments = Assignment.query.all()
    return jsonify([assignment.to_dict() for assignment in assignments]), 200


#Get all assignments for a lesson
@lecturer_bp.route("/lessons/<int:lesson_id>/assignments", methods=["GET"], endpoint="get_lesson_assignments")
@login_required
def get_assignments(lesson_id):
    """Retrieve all assignments for a specific lesson."""
    assignments = Assignment.query.filter_by(lesson_id=lesson_id).all()
    return jsonify([assignment.to_dict() for assignment in assignments]), 200



# Create a New Assignment
@lecturer_bp.route("/assignments/new", methods=["POST"], endpoint="add_assignment")
@login_required
def create_assignment():
    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    file = request.files.get("file") 

    if not title:
        return jsonify({"error": "Title is required"}), 400

    saved_file_path = None
    if file:
        saved_file_path, error = save_uploaded_file(file, is_assignment=True) 
        if error:
            return jsonify({"error": error}), 400

    new_assignment = Assignment(
        title=title,
        description=description,
        due_date=due_date,
        file_url=saved_file_path
    )

    db.session.add(new_assignment)
    db.session.commit()

    return jsonify({"message": "Assignment created successfully", "assignment": new_assignment.to_dict()}), 201


#Edit assignment
@lecturer_bp.route("/assignments/<int:assignment_id>", methods=["PUT"])
@login_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    data = request.form if request.form else request.get_json()
    file = request.files.get("file")

    if not data and not file:
        return jsonify({"error": "No data received!"}), 400

    updated = False

    title = data.get("title", assignment.title).strip()
    description = data.get("description", assignment.description).strip() if data.get("description") else None
    due_date = data.get("due_date", assignment.due_date)

    if title and title != assignment.title:
        assignment.title = title
        updated = True
    if description and description != assignment.description:
        assignment.description = description
        updated = True
    if due_date and due_date != str(assignment.due_date):
        assignment.due_date = due_date
        updated = True

    #File Upload
    if file:
        upload_folder = get_upload_folder()
        if assignment.file_url:
            old_file_path = os.path.abspath(os.path.join(upload_folder, assignment.file_url.replace("uploads/", "", 1)))
            if os.path.exists(old_file_path):
                print(f"🗑️ Deleting old file: {old_file_path}")
                os.remove(old_file_path)

        new_file_url, error = save_uploaded_file(file, is_assignment=True)
        if error:
            return jsonify({"error": error}), 400

        assignment.file_url = new_file_url
        updated = True

    if not updated:
        return jsonify({"message": "No changes made."}), 200

    db.session.commit()
    return jsonify({"message": "Assignment updated successfully", "assignment": assignment.to_dict()}), 200


#Delete an assignment
@lecturer_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"], endpoint="delete_assignment")
@login_required
def delete_assignment(assignment_id):
    """Delete an assignment and its associated file."""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.file_url:
        upload_folder = get_upload_folder()
        file_directory = os.path.join(upload_folder, "assignments")
        file_path = os.path.join(file_directory, assignment.file_url.split("/")[-1])

        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Assignment deleted successfully"}), 200

#Download unassigned assignment route
@lecturer_bp.route("/download/assignments/<path:filename>")
def download_assignment(filename):
    """Serve an assignment file for download."""
    upload_folder = get_upload_folder()
    file_directory = os.path.join(upload_folder, "assignments")
    file_path = os.path.join(file_directory, filename)

    print(f"Flask is trying to serve assignment file from: {file_path}")

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404, description=f"File not found at {file_path}")
