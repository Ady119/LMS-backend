"""Your next migration

Revision ID: 6134e15d3e6d
Revises: a6ea6a5a759b
Create Date: 2025-03-28 15:41:07.886936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6134e15d3e6d'
down_revision = 'a6ea6a5a759b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'users', ['lecturer_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('lecturer_id')

    # ### end Alembic commands ###
