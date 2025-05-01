# socket_handlers.py

from flask import request
from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import db, Message, Enrolment
import datetime

global_history = []

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        print("🔔 [join] received:", data)
        try:
            verify_jwt_in_request(locations=["cookies"])
            user_id = get_jwt_identity()
        except Exception as e:
            print("✋ [join] auth error:", e)
            emit("error", {"message": "Unauthorized"})
            return

        course_id = data.get("course_id") or "global"
        print(f"🔑 [join] user {user_id} joining room {course_id}")

        if course_id != "global":
            enrolled = db.session.query(Enrolment) \
                .filter_by(student_id=user_id, course_id=course_id) \
                .first()
            if not enrolled:
                print(f"✋ [join] user {user_id} not enrolled in {course_id}")
                emit("error", {"message": "Forbidden"})
                return

            room = f"course-{course_id}"
            history = [
                m.to_dict() for m in Message.query
                                            .filter_by(course_id=course_id)
                                            .order_by(Message.created_at)
                                            .all()
            ]
        else:
            room = "global"
            history = global_history

        join_room(room)
        emit("history", history)
        print(f"✅ [join] history sent to room {room}")

    @socketio.on("send_message")
    def handle_send_message(data):
        print("🔔 [send_message] received:", data)
        try:
            verify_jwt_in_request(locations=["cookies"])
            user_id = get_jwt_identity()
        except Exception as e:
            print("✋ [send_message] auth error:", e)
            emit("error", {"message": "Unauthorized"})
            return

        course_id = data.get("course_id") or "global"
        content = (data.get("content") or "").strip()
        if not content:
            print("✋ [send_message] empty content")
            emit("error", {"message": "Content required"})
            return

        print(f"📝 [send_message] user {user_id} says: {content} in {course_id}")

        if course_id != "global":
            enrolled = db.session.query(Enrolment) \
                .filter_by(student_id=user_id, course_id=course_id) \
                .first()
            if not enrolled:
                print(f"✋ [send_message] user {user_id} forbidden in {course_id}")
                emit("error", {"message": "Forbidden"})
                return

            # Persist
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

        # Broadcast
        emit("new_message", payload, room=room)
        print(f"✅ [send_message] broadcasted to {room}")

    @socketio.on("leave")
    def handle_leave(data):
        print("🔔 [leave] received:", data)
        course_id = data.get("course_id") or "global"
        room = f"course-{course_id}" if course_id != "global" else "global"
        leave_room(room)
        print(f"👋 [leave] left room {room}")
