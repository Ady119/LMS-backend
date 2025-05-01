from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_socketio         import join_room, leave_room, emit
from flask                  import request

from models import db, Message, Enrolment

def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        course_id = data.get("course_id")
        if not course_id:
            emit("error", {"message": "Missing course_id"})
            return

        # enrollment check
        if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
            emit("error", {"message": "Forbidden"})
            return

        room = f"course-{course_id}"
        join_room(room)

        # send history
        msgs = (
            Message.query
                   .filter_by(course_id=course_id)
                   .order_by(Message.created_at)
                   .all()
        )
        emit("history", [m.to_dict() for m in msgs])

    @socketio.on("send_message")
    def handle_send_message(data):
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        course_id = data.get("course_id")
        content   = (data.get("content") or "").strip()
        if not course_id or not content:
            emit("error", {"message": "course_id and content required"})
            return

        # enrollment check
        if not db.session.query(Enrolment).filter_by(
                student_id=user_id, course_id=course_id
            ).first():
            emit("error", {"message": "Forbidden"})
            return

        # persist & broadcast
        msg = Message(course_id=course_id, sender_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        payload = msg.to_dict()

        room = f"course-{course_id}"
        emit("new_message", payload, room=room)

    @socketio.on("leave")
    def handle_leave(data):
        cid = data.get("course_id")
        if cid:
            leave_room(f"course-{cid}")
