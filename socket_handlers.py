# socket_handlers.py

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_socketio      import join_room, leave_room, emit
from models import db, Message, Enrolment
import datetime

global_history = []

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        room = data.get("course_id") or "global"
        if room != "global":
            if not db.session.query(Enrolment).filter_by(student_id=user_id, course_id=room).first():
                emit("error", {"message": "Forbidden"})
                return

        join_room(room)

        if room == "global":
            emit("history", global_history)
        else:
            msgs = Message.query.filter_by(course_id=room).order_by(Message.created_at).all()
            emit("history", [m.to_dict() for m in msgs])

    @socketio.on("send_message")
    def handle_send_message(data):
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        room   = data.get("course_id") or "global"
        content = (data.get("content") or "").strip()
        if not content:
            emit("error", {"message": "content required"})
            return

        if room != "global":
            if not db.session.query(Enrolment).filter_by(student_id=user_id, course_id=room).first():
                emit("error", {"message": "Forbidden"})
                return
            msg = Message(course_id=room, sender_id=user_id, content=content)
            db.session.add(msg)
            db.session.commit()
            payload = msg.to_dict()
        else:
            payload = {
                "sender_id": user_id,
                "content": content,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            global_history.append(payload)

        emit("new_message", payload, room=room)

    @socketio.on("leave")
    def handle_leave(data):
        room = data.get("course_id") or "global"
        leave_room(room)
