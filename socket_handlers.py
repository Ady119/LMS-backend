from flask_socketio import join_room, leave_room, emit
from flask import request
from utils.tokens import decode_jwt
from models import db, Message, ChatRoom, Enrolment

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        token = request.cookies.get("access_token")
        if not token:
            return emit("error", {"message": "Not authenticated"})
        try:
            decoded = decode_jwt(token)
        except Exception:
            return emit("error", {"message": "Invalid or expired token"})
        user_id = decoded.get("user_id")
        if not user_id:
            return emit("error", {"message": "Malformed token"})

        course_id = data.get("course_id")
        if course_id:
            enrolled = Enrolment.query.filter_by(student_id=user_id, course_id=course_id).first()
            if not enrolled:
                return emit("error", {"message": "Forbidden"})
            room_obj = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
            if not room_obj:
                return emit("error", {"message": "Room not found"})
        else:
            room_obj = ChatRoom.query.filter_by(is_global=True).first()
            if not room_obj:
                return emit("error", {"message": "Global room not found"})

        room_name = f"chatroom-{room_obj.id}"
        join_room(room_name)

        history = (
            Message.query
            .filter_by(chat_room_id=room_obj.id)
            .order_by(Message.created_at)
            .all()
        )
        emit("history", [m.to_dict() for m in history])

    @socketio.on("send_message")
    def handle_send_message(data):
        token = request.cookies.get("access_token")
        if not token:
            return emit("error", {"message": "Not authenticated"})
        try:
            decoded = decode_jwt(token)
        except Exception:
            return emit("error", {"message": "Invalid or expired token"})
        user_id = decoded.get("user_id")
        if not user_id:
            return emit("error", {"message": "Malformed token"})

        course_id = data.get("course_id")
        content = (data.get("content") or "").strip()
        if not content:
            return emit("error", {"message": "Content required"})

        if course_id:
            enrolled = Enrolment.query.filter_by(student_id=user_id, course_id=course_id).first()
            if not enrolled:
                return emit("error", {"message": "Forbidden"})
            room_obj = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
        else:
            room_obj = ChatRoom.query.filter_by(is_global=True).first()

        if not room_obj:
            return emit("error", {"message": "Room not found"})

        msg = Message(chat_room_id=room_obj.id, sender_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()

        room_name = f"chatroom-{room_obj.id}"
        emit("new_message", msg.to_dict(), room=room_name)

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id")
        if course_id:
            room_obj = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
        else:
            room_obj = ChatRoom.query.filter_by(is_global=True).first()
        if room_obj:
            leave_room(f"chatroom-{room_obj.id}")
