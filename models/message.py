from models import db
from sqlalchemy.orm import relationship

class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"

    id = db.Column(db.Integer, primary_key=True)
    # If this room is tied to a course, course_id is set; otherwise it's a global or direct chat
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    # Mark a room as global chat
    is_global = db.Column(db.Boolean, default=False, nullable=False)
    # For private or group chats, you could add additional flags or participant tables

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    # Backref for messages
    messages = relationship(
        "Message",
        back_populates="chat_room",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    # Now reference chat_room instead of course directly
    chat_room_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chat_room = relationship("ChatRoom", back_populates="messages")

    sender_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "chat_room_id": self.chat_room_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }
