from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_socketio import join_room, leave_room, emit
from flask import request
from models import db, Message, ChatRoom, Enrolment


def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        course_id = data.get("course_id")
        if course_id:
            # Check enrollment
            enrolled = db.session.query(Enrolment).filter_by(
                student_id=user_id,
                course_id=course_id
            ).first()
            if not enrolled:
                return emit("error", {"message": "Forbidden"})
            room_obj = db.session.query(ChatRoom).filter_by(
                course_id=course_id,
                is_global=False
            ).first()
            if not room_obj:
                return emit("error", {"message": "Room not found"})
        else:
            # Global chat room
            room_obj = db.session.query(ChatRoom).filter_by(
                is_global=True
            ).first()
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
        # Ensure user is authenticated
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()

        course_id = data.get("course_id")
        content = (data.get("content") or "").strip()
        if not content:
            return emit("error", {"message": "Content required"})

        # Determine appropriate chat room
        if course_id:
            enrolled = db.session.query(Enrolment).filter_by(
                student_id=user_id,
                course_id=course_id
            ).first()
            if not enrolled:
                return emit("error", {"message": "Forbidden"})
            room_obj = db.session.query(ChatRoom).filter_by(
                course_id=course_id,
                is_global=False
            ).first()
        else:
            room_obj = db.session.query(ChatRoom).filter_by(is_global=True).first()

        if not room_obj:
            return emit("error", {"message": "Room not found"})

        msg = Message(
            chat_room_id=room_obj.id,
            sender_id=user_id,
            content=content
        )
        db.session.add(msg)
        db.session.commit()
        payload = msg.to_dict()

        room_name = f"chatroom-{room_obj.id}"
        emit("new_message", payload, room=room_name)

    @socketio.on("leave")
    def handle_leave(data):
        room_id = data.get("course_id")
        if room_id:
            room_obj = db.session.query(ChatRoom).filter_by(
                course_id=room_id,
                is_global=False
            ).first()
        else:
            room_obj = db.session.query(ChatRoom).filter_by(is_global=True).first()
        if room_obj:
            leave_room(f"chatroom-{room_obj.id}")
