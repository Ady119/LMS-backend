from alembic import op
import sqlalchemy as sa

revision = 'fa567f4d182e'
down_revision = '726288a19b9b'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_messages_course_id', 'messages', ['course_id'])

def downgrade():
    op.drop_index('ix_messages_course_id', table_name='messages')
    op.drop_table('messages')
