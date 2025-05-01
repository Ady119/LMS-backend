"""Drop old course_id FK and column from messages"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'zzzz_drop_old_course_id'
down_revision = 'bbdcc7b2749b'   # the ChatRoom migration
branch_labels = None
depends_on = None

def upgrade():
    # Drop the old FK constraint by name:
    op.drop_constraint('messages_ibfk_1', 'messages', type_='foreignkey')
    # Now drop the column
    op.drop_column('messages', 'course_id')

def downgrade():
    # (optionally) put it back
    op.add_column('messages',
        sa.Column('course_id', sa.Integer(), nullable=False)
    )
    op.create_foreign_key(
        'messages_ibfk_1',
        'messages', 'courses',
        ['course_id'], ['id'],
        ondelete='CASCADE'
    )
