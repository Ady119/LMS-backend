from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models
from models.users import User

from models.institutions import Institution
from models.degrees import Degree 
from models.academic_calendar import AcademicCalendar
from models.calendar_week import CalendarWeek
from models.enrolments import Enrolment

from models.course_lecturers import CourseLecturer
from models.courses import Course
from models.course_lessons import Lesson
from models.lesson_section import LessonSection

from models.quizzes import Quiz
from models.short_quiz import ShortAnswerQuestion
from models.multiple_choice import MultipleChoiceQuestion
from models.quiz_attempts import QuizAttempt
from models.quiz_attempts_answers import QuizAttemptAnswer
from models.quiz_results import QuizResult

from models.assignment import Assignment
from models.assignment_submission import AssignmentSubmission

from models.exams import Exam



