# socket_handlers.py

from flask_socketio import join_room, leave_room, emit
from flask import request
from flask_jwt_extended import decode_token
from flask_jwt_extended.exceptions import JWTDecodeError
from models import db, Message, Enrolment
import datetime

global_history = []
_sid_user = {}

def init_chat_socket_handlers(socketio):
    @socketio.on("connect")
    def _connect(auth):
        token = auth.get("token")
        if not token:
            return False
        try:
            data = decode_token(token)
        except JWTDecodeError:
            return False
        _sid_user[request.sid] = data["sub"]

    @socketio.on("disconnect")
    def _disconnect():
        _sid_user.pop(request.sid, None)

    @socketio.on("join")
    def handle_join(data):
        user_id = _sid_user.get(request.sid)
        if not user_id:
            emit("error", {"message": "Unauthorized"})
            return

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
        user_id = _sid_user.get(request.sid)
        if not user_id:
            emit("error", {"message": "Unauthorized"})
            return

        room = data.get("course_id") or "global"
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
