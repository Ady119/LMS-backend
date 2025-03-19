from models import db
from models import Course
from models import Enrollment

class EnrollmentManager:
    @staticmethod
    def enroll_student(course_id, user_id):
        course = Course.query.get(course_id)
        if course:
            enrollment = Enrollment(course_id=course_id, user_id=user_id)
            db.session.add(enrollment)
            course.enrollment_count += 1
            db.session.commit()
            return True
        return False

    @staticmethod
    def unenroll_student(course_id, user_id):
        course = Course.query.get(course_id)
        if course and course.enrollment_count > 0:
            enrollment = Enrollment.query.filter_by(course_id=course_id, user_id=user_id).first()
            if enrollment:
                db.session.delete(enrollment)
                course.enrollment_count -= 1
                db.session.commit()
                return True
        return False
