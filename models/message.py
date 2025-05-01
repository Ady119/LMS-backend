from models import db
from sqlalchemy.orm import relationship

class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"
    id           = db.Column(db.Integer, primary_key=True)
    course_id    = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    is_global    = db.Column(db.Boolean, default=False, nullable=False)
    created_at   = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    course       = relationship("Course", back_populates="chat_room")
    messages     = relationship(
        "Message",
        back_populates="chat_room",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self):
        return f"<ChatRoom {self.id} course={self.course_id}>"


class Message(db.Model):
    __tablename__ = "messages"
    id           = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id    = db.Column(db.Integer, nullable=False)
    content      = db.Column(db.Text, nullable=False)
    created_at   = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    chat_room    = relationship("ChatRoom", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id} room={self.chat_room_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "chat_room_id": self.chat_room_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }