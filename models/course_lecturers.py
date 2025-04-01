from models import db

class CourseLecturer(db.Model):
    __tablename__ = 'course_lecturers'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f"<CourseLecturer Course {self.course_id} Lecturer {self.lecturer_id}>"
