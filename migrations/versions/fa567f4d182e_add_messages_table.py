"""
Revision ID: 20250501_add_chat_rooms
Revises: <previous_revision_id>
Create Date: 2025-05-01 08:00:00.000000
"""
"""Create messages table

Revision ID: fa567f4d182e
Revises: 726288a19b9b
Create Date: 2025-05-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'fa567f4d182e'
down_revision = '726288a19b9b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chat_rooms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )

    op.add_column('messages', sa.Column('chat_room_id', sa.Integer(), sa.ForeignKey('chat_rooms.id', ondelete='CASCADE'), nullable=True, index=True))

    conn = op.get_bind()
    result = conn.execute(sa.text('SELECT id FROM courses'))
    course_ids = [row[0] for row in result]
    for cid in course_ids:
        conn.execute(sa.text(
            'INSERT INTO chat_rooms (course_id, is_global) VALUES (:cid, false)'
        ), {'cid': cid})
    for cid in course_ids:
        conn.execute(sa.text(
            'UPDATE messages SET chat_room_id = cr.id '
            'FROM chat_rooms cr WHERE cr.course_id = :cid AND messages.course_id = :cid'
        ), {'cid': cid})

    conn.execute(sa.text(
        "INSERT INTO chat_rooms (course_id, is_global) VALUES (NULL, true)"
    ))

    op.drop_index('ix_messages_course_id', table_name='messages')
    op.drop_constraint('messages_course_id_fkey', 'messages', type_='foreignkey')
    op.drop_column('messages', 'course_id')
