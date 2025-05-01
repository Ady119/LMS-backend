# socket_handlers.py

from flask_socketio import join_room, leave_room, emit
from flask import request
from utils.tokens import decode_jwt
from models import db, User, Message, ChatRoom, Enrolment, CourseLecturer, Course

def _message_with_sender(m: Message):
    user = User.query.get(m.sender_id)
    return { **m.to_dict(), "sender_name": user.username if user else None }

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        token = request.cookies.get("access_token")
        if not token:
            return emit("error", {"message": "Not authenticated"})
        try:
            decoded = decode_jwt(token)
        except:
            return emit("error", {"message": "Invalid or expired token"})
        user_id   = decoded["user_id"]
        user      = User.query.get(user_id)
        course_id = data.get("course_id")

        if course_id:
            allowed = False
            if user.role == 'student':
                allowed = Enrolment.query.filter_by(student_id=user_id, course_id=course_id).first()
            elif user.role == 'lecturer':
                allowed = CourseLecturer.query.filter_by(lecturer_id=user_id, course_id=course_id).first()
            if not allowed:
                return emit("error", {"message": "Forbidden"})

            room = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
            if not room:
                room = ChatRoom(course_id=course_id, is_global=False)
                db.session.add(room); db.session.commit()
        else:
            room = ChatRoom.query.filter_by(is_global=True).first()
            if not room:
                room = ChatRoom(is_global=True)
                db.session.add(room); db.session.commit()

        room_name = f"chatroom-{room.id}"
        join_room(room_name)
        history = Message.query.filter_by(chat_room_id=room.id).order_by(Message.created_at).all()
        emit("history", [_message_with_sender(m) for m in history])

    @socketio.on("send_message")
    def handle_send_message(data):
        token = request.cookies.get("access_token")
        if not token:
            return emit("error", {"message": "Not authenticated"})
        try:
            decoded = decode_jwt(token)
        except:
            return emit("error", {"message": "Invalid or expired token"})
        user_id   = decoded["user_id"]
        user      = User.query.get(user_id)
        course_id = data.get("course_id")
        content   = (data.get("content") or "").strip()
        if not content:
            return emit("error", {"message": "Content required"})

        if course_id:
            allowed = False
            if user.role == 'student':
                allowed = Enrolment.query.filter_by(student_id=user_id, course_id=course_id).first()
            elif user.role == 'lecturer':
                allowed = CourseLecturer.query.filter_by(lecturer_id=user_id, course_id=course_id).first()
            if not allowed:
                return emit("error", {"message": "Forbidden"})

            room = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
        else:
            room = ChatRoom.query.filter_by(is_global=True).first()

        if not room:
            return emit("error", {"message": "Room not found"})

        msg = Message(chat_room_id=room.id, sender_id=user_id, content=content)
        db.session.add(msg); db.session.commit()
        emit("new_message", _message_with_sender(msg), room=f"chatroom-{room.id}")

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id")
        room = (ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
                if course_id else ChatRoom.query.filter_by(is_global=True).first())
        if room:
            leave_room(f"chatroom-{room.id}")
