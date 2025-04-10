import os
import bleach
from werkzeug.utils import secure_filename, safe_join
from flask import Blueprint, jsonify, g, request, current_app, send_from_directory, abort, send_file
from sqlalchemy.orm import joinedload
from utils.tokens import get_jwt_token, decode_jwt
from utils.utils import login_required
from utils.dropbox_service import delete_file_from_dropbox, get_file_link, upload_file, get_temporary_download_link
import dropbox

from models.users import User, db
from models.announcements import Announcement
from models.courses import Course
from models.course_lecturers import CourseLecturer
from models.course_lessons import Lesson
from models.lesson_section import LessonSection
from models.quizzes import Quiz
from models.assignment import Assignment
from models.academic_calendar import AcademicCalendar
from models.calendar_week import CalendarWeek
from models.quiz_questions import QuizQuestion
from models.enrolments import Enrolment
from models.assignment_submission import AssignmentSubmission
from models.quiz_attempts import QuizAttempt
from models.degrees import Degree

# Lecturers' blueprint
lecturer_bp = Blueprint("lecturer", __name__)

def get_upload_folder():
    return current_app.config.get["AvhievED-LMS"]

@lecturer_bp.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", 
                  "http://127.0.0.1:5173", 
                  "http://localhost:4173",
                  "https://lms-frontend-5v355z5s0-adrians-projects-6add6cfa.vercel.app", 
                  "lms-frontend-henna-sigma.vercel.app"]:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

#______________________________________________* Courses *_________________________________________________

# fetch all courses
@lecturer_bp.route("/courses", methods=["GET"])
@login_required
def get_my_courses():
    lecturer_id = g.user.get("user_id")

    print(f"🔍 Lecturer ID: {lecturer_id}")

    if not lecturer_id:
        return jsonify({"error": "Invalid token"}), 401

    courses = db.session.query(
        Course.id, Course.title, Course.description
    ).join(CourseLecturer, Course.id == CourseLecturer.course_id
    ).filter(CourseLecturer.lecturer_id == lecturer_id).all()

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

#_______________________________________________ * Lessons *__________________________________________________

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

#Delete lesson section
@lecturer_bp.route('/courses/<int:course_id>/lessons/<int:lesson_id>/sections/<int:section_id>', methods=['DELETE'])
@login_required
def delete_section(course_id, lesson_id, section_id):
    section = LessonSection.query.filter_by(id=section_id, lesson_id=lesson_id).first()

    if not section:
        return jsonify({"error": "Section not found"}), 404

    if section.file_url:
        try:
            delete_file_from_dropbox(section.file_url)
            print(f" File deleted from Dropbox: {section.file_url}")
        except Exception as e:
            print(f" Error deleting file from Dropbox: {e}")

    # Delete progress records
    try:
        from models import SectionProgress
        SectionProgress.query.filter_by(section_id=section_id).delete()
        db.session.commit()
    except Exception as e:
        print(f" Error deleting section progress: {e}")
        return jsonify({"error": "Failed to delete related progress records"}), 500

    db.session.delete(section)
    db.session.commit()

    return jsonify({"message": "Section, file, and related progress deleted successfully"})



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

    sections = (
        LessonSection.query
        .options(joinedload(LessonSection.calendar_week))
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
                "assignment": section.assignment.to_dict() if section.assignment else None,
                "quiz": section.quiz.to_dict() if section.quiz else None,
                "calendar_week_id": section.calendar_week_id,
                "calendar_week_label": section.calendar_week.label if section.calendar_week else None,
                "is_current_week": section.is_current_week,
            }
            for section in sections
        ],
    }

    return jsonify(lesson_data), 200

#Upload a New Section
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/sections", methods=["POST"])
@login_required
def add_section(course_id, lesson_id):
    title = request.form.get("title")
    content_type = request.form.get("content_type")
    text_content = request.form.get("text_content", "").strip()
    file = request.files.get("file")
    assignment_id = request.form.get("assignment_id")
    quiz_id = request.form.get("quiz_id")
    calendar_week_id = request.form.get("calendar_week_id")
    if calendar_week_id:
        try:
            calendar_week_id = int(calendar_week_id)
            if not CalendarWeek.query.get(calendar_week_id):
                return jsonify({"error": "Invalid calendar_week_id"}), 400
        except ValueError:
            return jsonify({"error": "calendar_week_id must be an integer"}), 400

    if not title or not content_type:
        return jsonify({"error": "Title and content type are required"}), 400

    if assignment_id and quiz_id:
        return jsonify({"error": "Cannot assign both quiz and assignment to the same section"}), 400

    saved_file_url = None

    if file:
        # Upload file to Dropbox
        dropbox_folder = f"/AchievED-LMS/sections/course_{course_id}/lesson_{lesson_id}"
        saved_file_url, error = upload_file(file, folder_path=dropbox_folder)

        if error:
            return jsonify({"error": "File upload failed"}), 500

    # Sanitize text input
    allowed_tags = ["b", "i", "u", "strong", "em", "p", "br", "ul", "ol", "li", "a", "blockquote", "h1", "h2", "h3"]
    text_content = bleach.clean(text_content or "", tags=allowed_tags, strip=True)

    new_section = LessonSection(
    lesson_id=lesson_id,
    title=title,
    content_type=content_type,
    text_content=text_content,
    file_url=saved_file_url,
    assignment_id=assignment_id,
    quiz_id=quiz_id,
    calendar_week_id=calendar_week_id
)

    db.session.add(new_section)
    db.session.commit()

    return jsonify({
        "message": "Section added successfully",
        "section": new_section.to_dict()
    }), 201


#Edit section
#_________________________________________________________________________________________________
@lecturer_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/sections/<int:section_id>", methods=["PUT"])
@login_required
def edit_section(course_id, lesson_id, section_id):
    """Edit a lesson section, allowing file replacement via Dropbox."""

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
    calendar_week_id = data.get("calendar_week_id", section.calendar_week_id)
    if calendar_week_id:
        try:
            calendar_week_id = int(calendar_week_id)
            if not CalendarWeek.query.get(calendar_week_id):
                return jsonify({"error": "Invalid calendar_week_id"}), 400
        except ValueError:
            return jsonify({"error": "calendar_week_id must be an integer"}), 400
        
    file = request.files.get("file")
    file_url = section.file_url  

    if content_type == "file" and file:
        if section.file_url:
            try:
                dropbox_file_path = section.file_url.split("dl=1")[0]
                delete_file_from_dropbox(dropbox_file_path)
                print(f" Old file deleted from Dropbox: {dropbox_file_path}")

            except Exception as e:
                print(f" Error deleting old file from Dropbox: {e}")

        try:
            dropbox_folder = f"/AchievED-LMS/sections/course_{course_id}/lesson_{lesson_id}"
            file_url, error = upload_file(file, folder_path=dropbox_folder)

            if error:
                return jsonify({"error": "File upload failed"}), 500

            print(f"New file uploaded successfully: {file_url}")

        except Exception as e:
            print(f" Error uploading new file to Dropbox: {e}")
            return jsonify({"error": "File upload failed"}), 500

    # Sanitize text content
    allowed_tags = ["b", "i", "u", "strong", "em", "p", "br", "ul", "ol", "li", "a", "blockquote", "h1", "h2", "h3"]
    text_content = bleach.clean(text_content or "", tags=allowed_tags, strip=True)

    # Update section details
    section.title = title
    section.content_type = content_type
    section.calendar_week_id = calendar_week_id


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



#Serve Uploaded Files
@lecturer_bp.route("/download/course/<int:course_id>/lesson/<int:lesson_id>/<path:filename>")
@login_required
def download_file(course_id, lesson_id, filename):
    """Retrieve a lesson file's download link from Dropbox."""

    dropbox_folder = f"course_{course_id}/lesson_{lesson_id}"

    # Get the file link from Dropbox
    file_url = get_temporary_download_link(filename, folder=dropbox_folder)

    if not file_url:
        return jsonify({"error": "File not found"}), 404

    return jsonify({"message": "File available for download", "file_url": file_url})

#Fetch All Quizzes
@lecturer_bp.route("/quizzes", methods=["GET"])
@login_required
def get_all_quizzes():
    user_id = g.user.get("user_id")
    quizzes = Quiz.query.filter_by(lecturer_id=user_id).all()
    return jsonify([quiz.to_dict() for quiz in quizzes]), 200

#Fetch one single quiz
@lecturer_bp.route("/quizzes/<int:quiz_id>", methods=["GET"])
@login_required
def get_quiz(quiz_id):
    user_id = g.user.get("user_id")
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.lecturer_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify(quiz.to_dict()), 200

@lecturer_bp.route("/quizzes/<int:quiz_id>/view", methods=["GET"], endpoint="view_quiz_details")
@login_required
def get_quiz(quiz_id):
    user_id = g.user.get("user_id")
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.lecturer_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()

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
        "questions": [q.to_dict() for q in questions],
    }), 200


#CREATE a New Quiz
@lecturer_bp.route("/quizzes/new", methods=["POST"])
@login_required
def create_quiz():
    user_id = g.user.get("user_id")

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
        deadline=deadline,
        lecturer_id=user_id
    )

    db.session.add(new_quiz)
    db.session.commit()

    return jsonify({
        "message": "Quiz created successfully",
        "quiz": new_quiz.to_dict()
    }), 201

# EDIT a Quiz info
@lecturer_bp.route("/quizzes/<int:quiz_id>/edit", methods=["PUT"])
@login_required
def edit_quiz(quiz_id):
    user_id = g.user.get("user_id")

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    if quiz.lecturer_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json

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
@lecturer_bp.route("/quizzes/<int:quiz_id>/delete", methods=["DELETE"])
@login_required
def delete_quiz(quiz_id):
    user_id = g.user.get("user_id")

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    if quiz.lecturer_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(quiz)
    db.session.commit()

    return jsonify({"message": "Quiz deleted successfully"}), 200


# GET Questions for a Quiz (Both Types)
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions", methods=["GET"])
@login_required
def get_questions(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    questions = [
        {**q.to_dict(), "id": str(q.id)} for q in quiz.questions
    ]

    return jsonify({"questions": questions}), 200

# CREATE a Short-Answer Question
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/short-answer/new", methods=["POST"])
@login_required
def add_short_answer_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    data = request.json
    question_text = data.get("question_text")
    correct_answer = data.get("correct_answer")

    if not question_text or correct_answer is None:
        return jsonify({"error": "Invalid question data"}), 400

    question = QuizQuestion(
        quiz_id=quiz_id,
        question_text=question_text,
        question_type="short_answer",
        correct_answer=correct_answer,
        options=None
    )

    db.session.add(question)
    db.session.commit()

    return jsonify({
        "message": "Short-answer question added",
        "question": question.to_dict()
    }), 201

# CREATE a Multiple-Choice Question
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/multiple-choice/new", methods=["POST"])
@login_required
def add_multiple_choice_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    data = request.json
    question_text = data.get("question_text")
    options = data.get("options")
    correct_answer = data.get("correct_answer")

    if not question_text or not options or correct_answer is None:
        return jsonify({"error": "Invalid question data"}), 400

    if len(options) < 2:
        return jsonify({"error": "Multiple-choice questions need at least two options"}), 400

    question = QuizQuestion(
        quiz_id=quiz_id,
        question_text=question_text,
        question_type="multiple_choice",
        correct_answer=correct_answer,
        options=options
    )

    db.session.add(question)
    db.session.commit()

    return jsonify({
        "message": "Multiple-choice question added",
        "question": question.to_dict()
    }), 201

#Edit Answer Question
#_________________________________________________________________________________________________
@lecturer_bp.route("/quizzes/<int:quiz_id>/questions/<int:question_id>/edit", methods=["PUT"])
@login_required
def edit_quiz_question(quiz_id, question_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first()

    if not question:
        return jsonify({"error": "Question not found"}), 404

    data = request.json
    question_text = data.get("question_text")
    correct_answer = data.get("correct_answer")
    question_type = data.get("question_type", question.question_type)

    if not question_text or correct_answer is None:
        return jsonify({"error": "Missing fields"}), 400

    question.question_text = question_text
    question.correct_answer = correct_answer
    question.question_type = question_type

    if question_type == "multiple_choice":
        options = data.get("options")
        if not options or len(options) < 2:
            return jsonify({"error": "Multiple-choice questions need at least two options"}), 400
        question.options = options
    else:
        question.options = None

    db.session.commit()

    return jsonify({
        "message": "Question updated",
        "question": question.to_dict()
    }), 200

# DELETE a Short-Answer Question
@lecturer_bp.route("/quizzes/questions/<int:question_id>/delete", methods=["DELETE"])
@login_required
def delete_quiz_question(question_id):
    question = QuizQuestion.query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    db.session.delete(question)
    db.session.commit()

    return jsonify({"message": "Question deleted"}), 200




#                                            **ASSIGNMENTS**

#Get all assignments created by a lecturer (across courses)
@lecturer_bp.route("/assignments", methods=["GET"], endpoint="get_assignments")
@login_required
def get_available_assignments():
    user_id = g.user.get("user_id")
    assignments = Assignment.query.filter_by(lecturer_id=user_id).all()
    return jsonify([assignment.to_dict() for assignment in assignments]), 200


@lecturer_bp.route("/lessons/<int:lesson_id>/assignments", methods=["GET"], endpoint="get_lesson_assignments")
@login_required
def get_assignments(lesson_id):
    user_id = g.user.get("user_id")
    assignments = Assignment.query.filter_by(
        lesson_id=lesson_id,
        lecturer_id=user_id
    ).all()
    return jsonify([assignment.to_dict() for assignment in assignments]), 200

# Create a New Assignment
@lecturer_bp.route("/assignments/new", methods=["POST"], endpoint="add_assignment")
@login_required
def create_assignment():
    user_id = g.user.get("user_id")

    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    file = request.files.get("file")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    file_url = None
    dropbox_path = None

    if file:
        try:
            filename = secure_filename(file.filename)
            file_extension = os.path.splitext(filename)[1]

            if not file_extension:
                return jsonify({"error": "Invalid file format (no extension)"}), 400

            file_url, dropbox_path = upload_file(file, filename, folder="assignments")

            if not file_url or not dropbox_path:
                return jsonify({"error": "File upload failed"}), 500

            print(f"File uploaded successfully: {file_url}")

        except Exception as e:
            print(f"Error uploading file to Dropbox: {e}")
            return jsonify({"error": "File upload failed"}), 500

    new_assignment = Assignment(
        title=title,
        description=description,
        due_date=due_date,
        file_url=file_url,
        dropbox_path=dropbox_path,
        lecturer_id=user_id
    )

    db.session.add(new_assignment)
    db.session.commit()

    return jsonify({
        "message": "Assignment created successfully",
        "assignment": new_assignment.to_dict()
    }), 201

#Edit assignment
@lecturer_bp.route("/assignments/<int:assignment_id>", methods=["PUT"])
@login_required
def edit_assignment(assignment_id):
    user_id = g.user.get("user_id")
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.lecturer_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

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

    if file:
        filename = secure_filename(file.filename)

        if assignment.dropbox_path:
            try:
                delete_file_from_dropbox(assignment.dropbox_path)
                print(f"Old file deleted from Dropbox: {assignment.dropbox_path}")
            except Exception as e:
                print(f"Error deleting old file from Dropbox: {e}")

        try:
            public_url, dropbox_path = upload_file(file, filename, folder="assignments")
            if not public_url:
                return jsonify({"error": "File upload failed"}), 500

            assignment.file_url = public_url
            assignment.dropbox_path = dropbox_path
            updated = True

            print(f"New file uploaded successfully: {public_url}")

        except Exception as e:
            print(f"Error uploading new file to Dropbox: {e}")
            return jsonify({"error": "File upload failed"}), 500

    if not updated:
        return jsonify({"message": "No changes made."}), 200

    db.session.commit()
    return jsonify({
        "message": "Assignment updated successfully",
        "assignment": assignment.to_dict()
    }), 200

#Delete an assignment
@lecturer_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"], endpoint="delete_assignment")
@login_required
def delete_assignment(assignment_id):
    user_id = g.user.get("user_id")
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.lecturer_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    linked_sections = LessonSection.query.filter_by(assignment_id=assignment.id).all()
    for section in linked_sections:
        section.assignment_id = None
    db.session.commit()

    if assignment.dropbox_path:
        try:
            delete_file_from_dropbox(assignment.dropbox_path)
            print(f"File deleted from Dropbox: {assignment.dropbox_path}")
        except dropbox.exceptions.ApiError as e:
            print(f"Error deleting file from Dropbox: {e}")
            return jsonify({"error": "Failed to delete file from Dropbox"}), 500

    db.session.delete(assignment)
    db.session.commit()

    return jsonify({"message": "Assignment deleted successfully"}), 200

#Download unassigned assignment route
@lecturer_bp.route("/download/assignments/<path:filename>")
def download_assignment(filename):
    dropbox_folder = "assignments"

    try:
        file_url = get_temporary_download_link(filename, folder=dropbox_folder)
        
        if not file_url:
            print(f" ERROR: File not found in Dropbox: {filename}")
            return jsonify({"error": "File not found"}), 404

        print(f" File found: {file_url}")
        return jsonify({"message": "File available for download", "file_url": file_url})

    except Exception as e:
        print(f" ERROR retrieving file from Dropbox: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    
#Fetch calendar weeks for course
@lecturer_bp.route("/courses/<int:course_id>/calendar_weeks", methods=["GET"])
def get_calendar_weeks_for_course(course_id):
    course = Course.query.get_or_404(course_id)
    degree = course.degree
    calendar = degree.calendar

    if not calendar:
        return jsonify({"error": "No academic calendar assigned to this degree."}), 404

    weeks = CalendarWeek.query.filter_by(calendar_id=calendar.id).order_by(CalendarWeek.week_number).all()

    return jsonify([
        {
            "id": w.id,
            "week_number": w.week_number,
            "label": w.label,
            "start_date": str(w.start_date),
            "end_date": str(w.end_date),
            "is_break": w.is_break
        }
        for w in weeks
    ])

#lecturer dashboard stats
@lecturer_bp.route("/dashboard", methods=["GET"])
@login_required
def get_lecturer_dashboard():
    lecturer_id = g.user.get("user_id")

    course_ids = db.session.query(CourseLecturer.course_id).filter_by(lecturer_id=lecturer_id).subquery()

    # Get lessons only from these courses
    lessons = Lesson.query.filter(Lesson.course_id.in_(course_ids)).all()
    lesson_ids = [lesson.id for lesson in lessons]

    total_courses = db.session.query(CourseLecturer.course_id).filter_by(lecturer_id=lecturer_id).distinct().count()
    total_lessons = len(lessons)

    total_sections = LessonSection.query.filter(LessonSection.lesson_id.in_([l.id for l in lessons])).count()
    total_text_sections = LessonSection.query.filter(
        LessonSection.lesson_id.in_(lesson_ids),
        LessonSection.content_type == "text"
    ).count()
    total_quizzes = LessonSection.query.filter(
        LessonSection.lesson_id.in_(lesson_ids),
        LessonSection.quiz_id.isnot(None)
    ).count()
    total_assignments = LessonSection.query.filter(
        LessonSection.lesson_id.in_(lesson_ids),
        LessonSection.assignment_id.isnot(None)
    ).count()

    total_students = db.session.query(Enrolment.student_id).join(Degree).join(Course).filter(
        Course.id.in_(course_ids)
    ).distinct().count()

    total_submissions = AssignmentSubmission.query.join(Assignment).filter(
        Assignment.lecturer_id == lecturer_id
    ).count()

    total_quiz_attempts = QuizAttempt.query.join(Quiz).filter(
        Quiz.lecturer_id == lecturer_id
    ).count()

    avg_score_result = db.session.query(db.func.avg(QuizAttempt.score)).join(Quiz).filter(
        Quiz.lecturer_id == lecturer_id,
        QuizAttempt.score.isnot(None)
    ).scalar()
    avg_score = round(avg_score_result or 0, 2)

    return jsonify({
        "total_courses": total_courses,
        "total_lessons": total_lessons,
        "total_sections": total_sections,
        "total_text_sections": total_text_sections,
        "total_quizzes": total_quizzes,
        "total_assignments": total_assignments,
        "total_students": total_students,
        "total_submissions": total_submissions,
        "total_quiz_attempts": total_quiz_attempts,
        "avg_score": avg_score
    }), 200

#lecturer calendar
@lecturer_bp.route("/calendar", methods=["GET"])
@login_required
def get_lecturer_calendar_data():
    lecturer_id = g.user["user_id"]

    course_ids = db.session.query(CourseLecturer.course_id).filter_by(lecturer_id=lecturer_id).subquery()
    lessons = Lesson.query.filter(Lesson.course_id.in_(course_ids)).all()
    lesson_ids = [lesson.id for lesson in lessons]

    sections = LessonSection.query.filter(LessonSection.lesson_id.in_(lesson_ids)).all()

    events = []
    for section in sections:
        week = section.calendar_week
        if not week:
            continue

        events.append({
            "id": section.id,
            "title": f"{section.title} ({section.content_type})",
            "start": week.start_date.isoformat(),
            "end": week.end_date.isoformat(),
            "type": section.content_type,
            "is_break": week.is_break,
            "week_label": week.label,
        })

    # Include break weeks
    break_weeks = CalendarWeek.query.filter_by(is_break=True, calendar_id=lessons[0].course.degree.calendar_id).all() if lessons else []
    for week in break_weeks:
        events.append({
            "id": f"break-{week.id}",
            "title": f"{week.label} (Break)",
            "start": week.start_date.isoformat(),
            "end": week.end_date.isoformat(),
            "type": "break",
            "is_break": True,
            "week_label": week.label,
        })

    return jsonify(events), 200

#lecturer profile
@lecturer_bp.route("/profile", methods=["GET"])
@login_required
def get_lecturer_profile():
    user_id = g.user["user_id"]

    user = User.query.get(user_id)
    if not user or user.role != "lecturer":
        return jsonify({"error": "Unauthorized"}), 403

    # Assigned courses
    assigned_courses = (
        Course.query
        .join(CourseLecturer, Course.id == CourseLecturer.course_id)
        .filter(CourseLecturer.lecturer_id == user_id)
        .all()
    )

    course_list = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "created_at": course.created_at.isoformat()
        } for course in assigned_courses
    ]

    return jsonify({
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "institution_name": user.institution.name if user.institution else "N/A",
        "date_created": user.date_created.isoformat(),
        "assigned_courses": course_list
    }), 200
    
#create announcements
@lecturer_bp.route("/courses/<int:course_id>/announcements", methods=["POST"])
@login_required
def create_announcement(course_id):
    lecturer_id = g.user.get("user_id")
    data = request.get_json()
    title = data.get("title")
    message = data.get("message")

    is_assigned = db.session.query(CourseLecturer).filter_by(
        course_id=course_id,
        lecturer_id=lecturer_id
    ).first()

    if not is_assigned:
        return jsonify({"error": "You are not assigned to this course"}), 403

    # Create announcement
    announcement = Announcement(
        course_id=course_id,
        lecturer_id=lecturer_id,
        title=title,
        message=message
    )
    db.session.add(announcement)
    db.session.commit()

    return jsonify({"message": "Announcement created"}), 201


#fetch announ. for a course
@lecturer_bp.route("/courses/<int:course_id>/announcements", methods=["GET"])
@login_required
def get_course_announcements(course_id):
    announcements = (
        Announcement.query
        .filter_by(course_id=course_id)
        .order_by(Announcement.created_at.desc())
        .all()
    )

    return jsonify([
        {
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "created_at": a.created_at.isoformat()
        } for a in announcements
    ])
    
#update announ.
@lecturer_bp.route("/courses/<int:course_id>/announcements/<int:announcement_id>", methods=["PUT"])
@login_required
def update_announcement(course_id, announcement_id):
    lecturer_id = g.user.get("user_id")
    data = request.get_json()

    announcement = Announcement.query.filter_by(
        id=announcement_id,
        course_id=course_id,
        lecturer_id=lecturer_id
    ).first()

    if not announcement:
        return jsonify({"error": "Not found or unauthorized"}), 404

    announcement.title = data.get("title", announcement.title)
    announcement.message = data.get("message", announcement.message)

    db.session.commit()

    return jsonify({"message": "Announcement updated successfully"}), 200

#delete announ.
@lecturer_bp.route("/courses/<int:course_id>/announcements/<int:announcement_id>", methods=["DELETE"])
@login_required
def delete_announcement(course_id, announcement_id):
    lecturer_id = g.user.get("user_id")

    announcement = Announcement.query.filter_by(
        id=announcement_id,
        course_id=course_id,
        lecturer_id=lecturer_id
    ).first()

    if not announcement:
        return jsonify({"error": "Not found or unauthorized"}), 404

    db.session.delete(announcement)
    db.session.commit()

    return jsonify({"message": "Announcement deleted"}), 200

#get all announ.
@lecturer_bp.route("/announcements", methods=["GET"])
@login_required
def get_all_announcements():
    lecturer_id = g.user["user_id"]
    
    assigned_course_ids = db.session.query(CourseLecturer.course_id).filter_by(
        lecturer_id=lecturer_id
    ).subquery()

    announcements = (
        db.session.query(Announcement, Course.title)
        .join(Course, Course.id == Announcement.course_id)
        .filter(Announcement.course_id.in_(assigned_course_ids))
        .order_by(Announcement.created_at.desc())
        .all()
    )

    result = [
    {
        "id": ann.id,
        "title": ann.title,
        "message": ann.message,
        "created_at": ann.created_at.isoformat(),
        "course_title": course_title,
    }
    for ann, course_title in announcements
]


    return jsonify(result), 200