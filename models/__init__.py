from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models
from models.users import User

from models.institutions import Institution
from models.degrees import Degree 
from models.enrolments import Enrolment
from models.course_lecturers import CourseLecturer

from models.courses import Course
from models.course_lessons import Lesson
from models.quizzes import Quiz
from models.short_quiz import ShortAnswerQuestion
from models.multiple_choice import MultipleChoiceQuestion
from models.quiz_attempts import QuizAttempt
from models.quiz_attempts_answers import QuizAttemptAnswer
from models.quiz_results import QuizResult

from models.lesson_section import LessonSection
from models.assignment import Assignment
from models.exams import Exam



