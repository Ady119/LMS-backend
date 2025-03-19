"""empty message

Revision ID: 631672713add
Revises: 7dc849c7b053
Create Date: 2025-03-06 15:18:56.953582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '631672713add'
down_revision = '7dc849c7b053'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lesson_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('file_url', sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(None, 'course_lessons', ['lesson_id'], ['id'])

    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('course_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('max_attempts', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('time_limit', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('randomize_questions', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('immediate_feedback', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('passing_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('deadline', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(None, 'courses', ['course_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('deadline')
        batch_op.drop_column('passing_score')
        batch_op.drop_column('immediate_feedback')
        batch_op.drop_column('randomize_questions')
        batch_op.drop_column('time_limit')
        batch_op.drop_column('max_attempts')
        batch_op.drop_column('course_id')

    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('file_url')
        batch_op.drop_column('lesson_id')

    # ### end Alembic commands ###
