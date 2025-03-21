import csv
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from models.courses import Course, db
from werkzeug.security import generate_password_hash
from models.users import User
from models.degrees import Degree
from models.enrolments import Enrolment
from models.course_lecturers import CourseLecturer
from models.academic_calendar import AcademicCalendar
from models.calendar_week import CalendarWeek
 
from utils.utils import login_required

admin_bp = Blueprint('admin', __name__)

# Helper function to get authorized course
def get_authorized_course(course_id, user_id):
    return Course.query.filter_by(id=course_id, instructor_id=user_id).first()

@admin_bp.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173", "lms-frontend-henna-sigma.vercel.app"]:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@admin_bp.route('/register', methods=['POST'])
@login_required
def register():
    if g.user.get("role") != "admin":
        return jsonify({"error": "Unauthorized: Only admins can register users."}), 403

    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    role = data.get("role", "student")

    if not username or not email or not password or not full_name:
        return jsonify({"error": "All fields are required"}), 400

    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        institution_id=g.user.get("institution_id")
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201


@admin_bp.route("/users", methods=["POST"])
@login_required
def add_user():
    """Admin can add a new user (Lecturer or Student)."""
    if g.user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    # Extract user details
    username = data.get("username")
    email = data.get("email")
    full_name = data.get("full_name")
    role = data.get("role")
    password = data.get("password") 
    institution_id = data.get("institution_id", None)

    if not username or not email or not full_name or not role or not password:
        return jsonify({"error": "All fields except institution_id are required"}), 400

    if role not in ["lecturer", "student"]:
        return jsonify({"error": "Invalid role. Must be 'lecturer' or 'student'"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists"}), 409

    password_hash = generate_password_hash(password)

    # Create the new user
    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        institution_id=institution_id
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!", "user_id": new_user.id}), 201


@admin_bp.route('/degrees', methods=['GET', 'POST'])
@login_required
def manage_degrees():
    if request.method == 'GET':
        degrees = Degree.query.all()
        return jsonify([degree.to_dict() for degree in degrees]), 200

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"error": "Degree name is required"}), 400

    degree = Degree(name=name, institution_id=g.user.get("institution_id"))
    db.session.add(degree)
    db.session.commit()

    return jsonify({"message": f"Degree '{degree.name}' created"}), 201

@admin_bp.route('/courses', methods=['GET'])
@login_required
def get_courses():
    courses = Course.query.all()
    print("Fetched Courses:", courses) 
    return jsonify([course.to_dict() for course in courses]), 200

@admin_bp.route('/courses', methods=['POST'])
@login_required
def add_course():
    if g.user.get('role') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    degree_id = data.get('degree_id')

    if not title or not degree_id:
        return jsonify({"error": "Title and degree ID are required"}), 400

    new_course = Course(
        title=title,
        description=description,
        degree_id=degree_id,
        institution_id=g.user.get('institution_id')
    )

    db.session.add(new_course)
    db.session.commit()

    return jsonify({"message": "Course added successfully!", "course_id": new_course.id}), 201

#assign lecturer/s to course
@admin_bp.route('/assign-lecturer', methods=['POST'])
@login_required
def assign_lecturer():
    if g.user.get('role') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    lecturer_id = data.get("lecturer_id")
    course_id = data.get("course_id")

    if not lecturer_id or not course_id:
        return jsonify({"error": "Lecturer ID and Course ID are required"}), 400

    print("Received lecturer_id:", lecturer_id, "Received course_id:", course_id)

    lecturer = User.query.filter_by(id=lecturer_id, role='lecturer').first()
    course = Course.query.get(course_id)

    if not lecturer:
        return jsonify({"error": "Invalid lecturer or not a lecturer"}), 400
    if not course:
        return jsonify({"error": "Invalid course"}), 400

    existing_assignment = CourseLecturer.query.filter_by(course_id=course_id, lecturer_id=lecturer_id).first()
    if existing_assignment:
        return jsonify({"error": "Lecturer already assigned to this course"}), 409

    course_lecturer = CourseLecturer(course_id=course_id, lecturer_id=lecturer_id)
    db.session.add(course_lecturer)
    db.session.commit()

    return jsonify({"message": f"Lecturer {lecturer.full_name} assigned to {course.title}."}), 200


#enrol/add student to a course
@admin_bp.route('/enrol-student', methods=['POST'])
def enrol_student():
    data = request.get_json()
    student_id = data.get("student_id")
    degree_id = data.get("degree_id")

    if not student_id or not degree_id:
        return jsonify({"error": "Missing student_id or degree_id"}), 400

    student = User.query.get(student_id)
    degree = Degree.query.get(degree_id)

    if not student or not degree:
        return jsonify({"error": "Invalid student or degree"}), 404

    # Check if student is already enrolled in the degree
    existing_enrolment = Enrolment.query.filter_by(student_id=student_id, degree_id=degree_id).first()
    if existing_enrolment:
        return jsonify({"error": "Student is already enrolled in this degree"}), 400

    enrolment = Enrolment(student_id=student_id, degree_id=degree_id)  
    db.session.add(enrolment)
    db.session.commit()

    return jsonify({"message": "Student successfully enrolled in degree"}), 200

#fetch the degrees a student is enrolled in 
@admin_bp.route('/enrolled-degrees/<int:student_id>', methods=['GET'])
def get_enrolled_degrees(student_id):
    enrolments = db.session.query(
        Degree.id.label("degree_id"),
        Degree.name
    ).join(Enrolment, Degree.id == Enrolment.degree_id).filter(
        Enrolment.student_id == student_id
    ).all()

    # Ensure each row is converted to a dictionary correctly
    return jsonify({
        "enrolled_degrees": [{"degree_id": row.degree_id, "name": row.name} for row in enrolments]
    })


# Retrieve all students
@admin_bp.route('/users/students', methods=['GET'])
@login_required
def get_students():
    if g.user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    students = User.query.filter(User.role == "student").all()
    return jsonify({"students": [student.to_dict() for student in students]}), 200
    
# Retrieve all lecturers
@admin_bp.route('/users/lecturers', methods=['GET'])
@login_required
def get_lecturers():
    lecturers = User.query.filter_by(role="lecturer").all()

    if not lecturers:
        return jsonify({"error": "No lecturers found"}), 404

    print("Lecturers in DB:", [lecturer.to_dict() for lecturer in lecturers])

    return jsonify([lecturer.to_dict() for lecturer in lecturers]), 200

#upload calendar
@admin_bp.route('/upload_calendar', methods=['POST'])
def upload_calendar():
    file = request.files.get('file')
    calendar_name = request.form.get('calendar_name')
    degree_id = request.form.get('degree_id')

    if not file or not calendar_name:
        return jsonify({"error": "File and calendar name are required"}), 400

    try:
        decoded = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)
        weeks = []
        start_dates = []

        for row in reader:
            week_number = int(row['Week'])
            start_date = datetime.strptime(row['Start Date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(row['End Date'], '%Y-%m-%d').date()

            if start_date > end_date:
                return jsonify({"error": f"Start date after end date in Week {week_number}"}), 400

            weeks.append({
                'week_number': week_number,
                'start_date': start_date,
                'end_date': end_date,
                'label': f"Week {week_number}"
            })
            start_dates.append(start_date)

        # Create AcademicCalendar
        calendar = AcademicCalendar(
            name=calendar_name,
            start_date=min(start_dates),
            end_date=max([w['end_date'] for w in weeks])
        )
        db.session.add(calendar)
        db.session.flush()

        # Create CalendarWeek entries
        for w in weeks:
            db.session.add(CalendarWeek(
                calendar_id=calendar.id,
                week_number=w['week_number'],
                start_date=w['start_date'],
                end_date=w['end_date'],
                label=w['label']
            ))

        if degree_id:
            degree = Degree.query.get(degree_id)
            if not degree:
                return jsonify({"error": "Degree not found"}), 404
            degree.calendar_id = calendar.id

        db.session.commit()
        return jsonify({"message": "Calendar uploaded successfully", "calendar_id": calendar.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500
    

@admin_bp.route('/api/admin/calendars/<int:calendar_id>', methods=['GET'])
def get_calendar_weeks(calendar_id):
    from models import AcademicCalendar, CalendarWeek

    calendar = AcademicCalendar.query.get_or_404(calendar_id)
    weeks = CalendarWeek.query.filter_by(calendar_id=calendar.id).order_by(CalendarWeek.week_number).all()

    return jsonify({
        "calendar_id": calendar.id,
        "name": calendar.name,
        "start_date": str(calendar.start_date),
        "end_date": str(calendar.end_date),
        "weeks": [{
            "week_number": w.week_number,
            "start_date": str(w.start_date),
            "end_date": str(w.end_date),
            "label": w.label
        } for w in weeks]
    })
