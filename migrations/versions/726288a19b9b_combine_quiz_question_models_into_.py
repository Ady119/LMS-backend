"""Combine quiz question models into QuizQuestion

Revision ID: 726288a19b9b
Revises: fdab085f6eaa
Create Date: 2025-04-07 21:56:25.190725

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '726288a19b9b'
down_revision = 'fdab085f6eaa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass  
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('multiple_choice_questions',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('quiz_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('question_text', mysql.TEXT(), nullable=False),
    sa.Column('options', mysql.LONGTEXT(charset='utf8mb4', collation='utf8mb4_bin'), nullable=False),
    sa.Column('correct_answer', mysql.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name='multiple_choice_questions_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_general_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('short_answer_questions',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('quiz_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('question_text', mysql.TEXT(), nullable=False),
    sa.Column('correct_answer', mysql.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name='short_answer_questions_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_general_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###
