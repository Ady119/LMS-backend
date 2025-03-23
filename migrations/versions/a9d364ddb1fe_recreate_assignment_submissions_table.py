from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9d364ddb1fe'
down_revision = 'e766a63843a6'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('assignment_submissions')  # Drop the old table if it exists

    op.create_table(
        'assignment_submissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('assignments.id'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_url', sa.String(length=255), nullable=False),
        sa.Column('original_file_name', sa.String(length=255), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.current_timestamp())
    )


def downgrade():
    op.drop_table('assignment_submissions')
