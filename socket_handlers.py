# socket_handlers.py

from flask import request
from flask_socketio import join_room, leave_room, emit
from utils.tokens import decode_jwt
from models import db, Message, Enrolment
import datetime

global_history = []

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        token = request.cookies.get("access_token")
        if not token:
            emit("error", {"message": "Unauthorized"})
            return {"status": "error", "reason": "no_token"}

        decoded = decode_jwt(token)
        if not decoded or not decoded.get("user_id"):
            emit("error", {"message": "Unauthorized"})
            return {"status": "error", "reason": "invalid_token"}

        user_id = decoded["user_id"]
        course_id = data.get("course_id") or "global"
        room = f"course-{course_id}" if course_id != "global" else "global"

        if course_id != "global":
            if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
                emit("error", {"message": "Forbidden"})
                return {"status": "error", "reason": "forbidden"}

            msgs = (
                Message.query
                       .filter_by(course_id=course_id)
                       .order_by(Message.created_at)
                       .all()
            )
            history = [m.to_dict() for m in msgs]
        else:
            history = global_history

        join_room(room)
        emit("history", history)
        return {"status": "ok"}

    @socketio.on("send_message")
    def handle_send_message(data):
        token = request.cookies.get("access_token")
        if not token:
            emit("error", {"message": "Unauthorized"})
            return {"status": "error", "reason": "no_token"}

        decoded = decode_jwt(token)
        if not decoded or not decoded.get("user_id"):
            emit("error", {"message": "Unauthorized"})
            return {"status": "error", "reason": "invalid_token"}

        user_id = decoded["user_id"]
        course_id = data.get("course_id") or "global"
        content = (data.get("content") or "").strip()
        if not content:
            emit("error", {"message": "Content required"})
            return {"status": "error", "reason": "no_content"}

        if course_id != "global":
            if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
                emit("error", {"message": "Forbidden"})
                return {"status": "error", "reason": "forbidden"}

            msg = Message(course_id=course_id, sender_id=user_id, content=content)
            db.session.add(msg)
            db.session.commit()
            payload = msg.to_dict()
            room = f"course-{course_id}"
        else:
            payload = {
                "sender_id": user_id,
                "content": content,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            global_history.append(payload)
            room = "global"

        emit("new_message", payload, room=room)
        return {"status": "ok"}

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id") or "global"
        room = f"course-{course_id}" if course_id != "global" else "global"
        leave_room(room)
        return {"status": "ok"}
