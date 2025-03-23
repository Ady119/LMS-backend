"""Initial migration after reset

Revision ID: 5058a710faea
Revises: 
Create Date: 2025-03-23 19:12:57.619613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5058a710faea'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('academic_calendars',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assignments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('file_url', sa.String(length=255), nullable=True),
    sa.Column('dropbox_path', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('institutions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('name')
    )
    op.create_table('quizzes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('max_attempts', sa.Integer(), nullable=True),
    sa.Column('time_limit', sa.Integer(), nullable=True),
    sa.Column('randomize_questions', sa.Boolean(), nullable=False),
    sa.Column('immediate_feedback', sa.Boolean(), nullable=False),
    sa.Column('passing_score', sa.Float(), nullable=True),
    sa.Column('deadline', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('calendar_weeks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('calendar_id', sa.Integer(), nullable=False),
    sa.Column('week_number', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=False),
    sa.Column('is_break', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['calendar_id'], ['academic_calendars.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('calendar_id', 'week_number', name='uq_calendar_week')
    )
    op.create_table('degrees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('institution_id', sa.Integer(), nullable=False),
    sa.Column('calendar_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['calendar_id'], ['academic_calendars.id'], ),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('multiple_choice_questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quiz_id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('options', sa.JSON(), nullable=False),
    sa.Column('correct_answer', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('short_answer_questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quiz_id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('correct_answer', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('institution_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('assignment_submissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('assignment_id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('file_url', sa.String(length=255), nullable=False),
    sa.Column('original_file_name', sa.String(length=255), nullable=True),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('courses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('institution_id', sa.Integer(), nullable=False),
    sa.Column('degree_id', sa.Integer(), nullable=True),
    sa.Column('thumbnail_url', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['degree_id'], ['degrees.id'], ),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('enrolments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('degree_id', sa.Integer(), nullable=False),
    sa.Column('enrolled_at', sa.DateTime(), nullable=False),
    sa.Column('progress', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['degree_id'], ['degrees.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quiz_attempts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('quiz_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('pass_status', sa.Boolean(), nullable=True),
    sa.Column('attempts_used', sa.Integer(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('needs_review', sa.Boolean(), nullable=False),
    sa.Column('answers_temp', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('course_lecturers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('lecturer_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['lecturer_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('course_lessons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('total_marks', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quiz_attempt_answers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('attempt_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('answer_text', sa.Text(), nullable=False),
    sa.Column('is_correct', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quiz_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('attempt_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lesson_section',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('quiz_id', sa.Integer(), nullable=True),
    sa.Column('assignment_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=50), nullable=False),
    sa.Column('text_content', sa.Text(), nullable=True),
    sa.Column('file_url', sa.String(length=255), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('calendar_week_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('(quiz_id IS NULL OR assignment_id IS NULL)', name='check_only_one_content_type'),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
    sa.ForeignKeyConstraint(['calendar_week_id'], ['calendar_weeks.id'], ),
    sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lesson_section')
    op.drop_table('quiz_results')
    op.drop_table('quiz_attempt_answers')
    op.drop_table('exams')
    op.drop_table('course_lessons')
    op.drop_table('course_lecturers')
    op.drop_table('quiz_attempts')
    op.drop_table('enrolments')
    op.drop_table('courses')
    op.drop_table('assignment_submissions')
    op.drop_table('users')
    op.drop_table('short_answer_questions')
    op.drop_table('multiple_choice_questions')
    op.drop_table('degrees')
    op.drop_table('calendar_weeks')
    op.drop_table('quizzes')
    op.drop_table('institutions')
    op.drop_table('assignments')
    op.drop_table('academic_calendars')
    # ### end Alembic commands ###
