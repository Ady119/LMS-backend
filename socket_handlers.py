# socket_handlers.py

from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import db, Message, Enrolment
import datetime

# Keep an in-memory history for the global chat
global_history = []

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        # Authenticate
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        # Determine room: course-specific or global
        course_id = data.get("course_id") or "global"
        if course_id != "global":
            # Enrollment check
            if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
                emit("error", {"message": "Forbidden"})
                return

            room = f"course-{course_id}"
            # Fetch persisted history
            msgs = (
                Message.query
                       .filter_by(course_id=course_id)
                       .order_by(Message.created_at)
                       .all()
            )
            history = [m.to_dict() for m in msgs]
        else:
            room = "global"
            history = global_history

        join_room(room)
        emit("history", history)
        return {"status": "ok"}

    @socketio.on("send_message")
    def handle_send_message(data):
        # Authenticate
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        course_id = data.get("course_id") or "global"
        content = (data.get("content") or "").strip()
        if not content:
            emit("error", {"message": "content required"})
            return

        if course_id != "global":
            # Enrollment check
            if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
                emit("error", {"message": "Forbidden"})
                return

            # Persist to database
            msg = Message(course_id=course_id, sender_id=user_id, content=content)
            db.session.add(msg)
            db.session.commit()
            payload = msg.to_dict()
            room = f"course-{course_id}"
        else:
            # Global room: just keep in memory
            payload = {
                "sender_id": user_id,
                "content": content,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            global_history.append(payload)
            room = "global"

        # Broadcast to the room
        emit("new_message", payload, room=room)
        return {"status": "ok"}

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id") or "global"
        room = f"course-{course_id}" if course_id != "global" else "global"
        leave_room(room)
        return {"status": "ok"}
