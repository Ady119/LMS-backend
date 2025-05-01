# socket_handlers.py

from flask import request
from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import db, Message, Enrolment
import datetime

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        try:
            verify_jwt_in_request(locations=["cookies"])
            user_id = get_jwt_identity()
        except Exception as e:
            print("✋ [join] auth failed:", e)
            emit("error", {"message": "Unauthorized"})
            return {"status": "error", "reason": "unauthorized"}

        course_id = data.get("course_id")
        if not course_id:
            print("✋ [join] missing course_id")
            emit("error", {"message": "course_id required"})
            return {"status": "error", "reason": "no_course_id"}

        enrolled = db.session.query(Enrolment) \
            .filter_by(student_id=user_id, course_id=course_id) \
            .first()
        if not enrolled:
            print(f"✋ [join] user {user_id} not enrolled in {course_id}")
            emit("error", {"message": "Forbidden"})
            return {"status": "error", "reason": "forbidden"}

        room = f"course-{course_id}"
        join_room(room)
        print(f"✅ [join] user {user_id} joined room {room}")

        history = Message.query \
            .filter_by(course_id=course_id) \
            .order_by(Message.created_at) \
            .all()
        emit("history", [m.to_dict() for m in history])

        return {"status": "ok"}

    @socketio.on("send_message")
    def handle_send_message(data):
        try:
            verify_jwt_in_request(locations=["cookies"])
            user_id = get_jwt_identity()
        except Exception as e:
            print("✋ [send] auth failed:", e)
            emit("error", {"message": "Unauthorized"})
            return {"status": "error", "reason": "unauthorized"}

        course_id = data.get("course_id")
        content = (data.get("content") or "").strip()
        if not course_id or not content:
            print("✋ [send] missing course_id or empty content")
            emit("error", {"message": "course_id and content required"})
            return {"status": "error", "reason": "invalid_payload"}

        enrolled = db.session.query(Enrolment) \
            .filter_by(student_id=user_id, course_id=course_id) \
            .first()
        if not enrolled:
            print(f"✋ [send] user {user_id} forbidden in {course_id}")
            emit("error", {"message": "Forbidden"})
            return {"status": "error", "reason": "forbidden"}

        # Persist message
        msg = Message(course_id=course_id, sender_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        payload = msg.to_dict()

        room = f"course-{course_id}"
        emit("new_message", payload, room=room)
        print(f"✅ [send] user {user_id} sent to {room}: {content}")

        return {"status": "ok"}

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id")
        if course_id:
            room = f"course-{course_id}"
            leave_room(room)
            print(f"👋 [leave] left room {room}")
        return {"status": "ok"}
