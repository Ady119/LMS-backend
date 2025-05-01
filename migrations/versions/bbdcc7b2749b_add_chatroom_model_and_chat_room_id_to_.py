"""Add ChatRoom model and chat_room_id to Message

Revision ID: bbdcc7b2749b
Revises: fa567f4d182e
Create Date: 2025-05-01 09:30:45.899314

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bbdcc7b2749b'
down_revision = 'fa567f4d182e'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create the chat_rooms table
    op.create_table(
        'chat_rooms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # 2) Add chat_room_id column to messages
    op.add_column('messages', sa.Column('chat_room_id', sa.Integer(), nullable=False, index=True))
    op.create_foreign_key(
        None, 'messages', 'chat_rooms',
        local_cols=['chat_room_id'], remote_cols=['id'], ondelete='CASCADE'
    )

    # 3) (Optional) Backfill: map old messages to their new chat_rooms
    conn = op.get_bind()
    conn.execute(sa.text("""
      INSERT INTO chat_rooms (course_id, is_global)
        SELECT DISTINCT course_id, FALSE FROM messages;
    """))
    conn.execute(sa.text("""
      UPDATE messages m
        JOIN chat_rooms cr ON cr.course_id = m.course_id
      SET m.chat_room_id = cr.id;
    """))

    # 4) Now remove the old FK+index+column in batch mode
    with op.batch_alter_table('messages', reflect=True) as batch_op:
        batch_op.drop_constraint('messages_ibfk_1', type_='foreignkey')   # adjust name if yours differs
        batch_op.drop_index('ix_messages_course_id')
        batch_op.drop_column('course_id')


def downgrade():
    # reverse in batch
    with op.batch_alter_table('messages', reflect=True) as batch_op:
        batch_op.add_column(sa.Column('course_id', mysql.INTEGER(display_width=11), nullable=False))
        batch_op.create_foreign_key('messages_ibfk_1', 'courses', ['course_id'], ['id'], ondelete='CASCADE')
        batch_op.create_index('ix_messages_course_id', ['course_id'], unique=False)
        batch_op.drop_constraint(None, type_='foreignkey')   # chat_room FK
        batch_op.drop_index(batch_op.f('ix_messages_chat_room_id'))
        batch_op.drop_column('chat_room_id')

    op.drop_table('chat_rooms')
