# socket_handlers.py

from flask import request
from flask_socketio import join_room, leave_room, emit
from utils.tokens import decode_jwt         # your custom JWT helper
from models import db, Message, Enrolment
import datetime

# Keep in-memory history for global chat
global_history = []

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        # 1) Authenticate
        token = request.cookies.get("access_token")
        if not token:
            emit("error", {"message": "Unauthorized: no token"})
            return

        decoded = decode_jwt(token)
        if not decoded:
            emit("error", {"message": "Unauthorized: invalid token"})
            return

        user_id = decoded.get("user_id")
        if not user_id:
            emit("error", {"message": "Unauthorized: missing user_id"})
            return

        # 2) Determine room
        course_id = data.get("course_id") or "global"
        room = f"course-{course_id}" if course_id != "global" else "global"

        # 3) Enrollment check (only for course rooms)
        if course_id != "global":
            if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
                emit("error", {"message": "Forbidden"})
                return

            # persisted history
            msgs = (
                Message.query
                       .filter_by(course_id=course_id)
                       .order_by(Message.created_at)
                       .all()
            )
            history = [m.to_dict() for m in msgs]
        else:
            history = global_history

        # 4) Join & send history
        join_room(room)
        emit("history", history)

    @socketio.on("send_message")
    def handle_send_message(data):
        # 1) Authenticate
        token = request.cookies.get("access_token")
        if not token:
            emit("error", {"message": "Unauthorized: no token"})
            return

        decoded = decode_jwt(token)
        if not decoded:
            emit("error", {"message": "Unauthorized: invalid token"})
            return

        user_id = decoded.get("user_id")
        if not user_id:
            emit("error", {"message": "Unauthorized: missing user_id"})
            return

        # 2) Payload validation
        course_id = data.get("course_id") or "global"
        content = (data.get("content") or "").strip()
        if not content:
            emit("error", {"message": "Content required"})
            return

        # 3) Enrollment check for course rooms
        if course_id != "global":
            if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
                emit("error", {"message": "Forbidden"})
                return

            # persist to DB
            msg = Message(course_id=course_id, sender_id=user_id, content=content)
            db.session.add(msg)
            db.session.commit()
            payload = msg.to_dict()
            room = f"course-{course_id}"
        else:
            # global chat
            payload = {
                "sender_id": user_id,
                "content": content,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            global_history.append(payload)
            room = "global"

        # 4) Broadcast
        emit("new_message", payload, room=room)

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id") or "global"
        room = f"course-{course_id}" if course_id != "global" else "global"
        leave_room(room)
