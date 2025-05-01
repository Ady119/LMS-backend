# chat.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import join_room, leave_room, emit
from models import db, Message, ChatRoom, Enrolment, Course
from utils.tokens import decode_jwt

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/rooms', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_rooms():
    user_id = get_jwt_identity()
    rooms = []
    global_room = ChatRoom.query.filter_by(is_global=True).first()
    if global_room:
        rooms.append({'id': global_room.id, 'name': 'Global', 'is_global': True})
    enrollments = Enrolment.query.filter_by(student_id=user_id).all()
    for e in enrollments:
        room = ChatRoom.query.filter_by(course_id=e.course_id, is_global=False).first()
        if room:
            rooms.append({'id': room.id, 'name': f'Course {e.course_id}', 'is_global': False})
    return jsonify(rooms), 200

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_room_messages(room_id):
    user_id = get_jwt_identity()
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if not room.is_global:
        allowed = (
            db.session.query(Course)
            .join(Enrolment, Course.degree_id == Enrolment.degree_id)
            .filter(Enrolment.student_id == user_id, Course.id == room.course_id)
            .first()
        )
        if not allowed:
            return jsonify({'error': 'Forbidden'}), 403
    msgs = Message.query.filter_by(chat_room_id=room_id).order_by(Message.created_at).all()
    return jsonify([m.to_dict() for m in msgs]), 200

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['POST'])
@jwt_required(locations=['cookies'])
def post_message(room_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Content required'}), 400
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if not room.is_global:
        allowed = (
            db.session.query(Course)
            .join(Enrolment, Course.degree_id == Enrolment.degree_id)
            .filter(Enrolment.student_id == user_id, Course.id == room.course_id)
            .first()
        )
        if not allowed:
            return jsonify({'error': 'Forbidden'}), 403
    msg = Message(chat_room_id=room_id, sender_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201


def init_chat_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        token = request.cookies.get("access_token")
        if not token:
            return emit("error", {"message": "Not authenticated"})
        try:
            decoded = decode_jwt(token)
        except:
            return emit("error", {"message": "Invalid or expired token"})
        user_id = decoded.get("user_id")
        course_id = data.get("course_id")
        if course_id:
            allowed = (
                db.session.query(Course)
                .join(Enrolment, Course.degree_id == Enrolment.degree_id)
                .filter(Enrolment.student_id == user_id, Course.id == course_id)
                .first()
            )
            if not allowed:
                return emit("error", {"message": "Forbidden"})
            room_obj = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
        else:
            room_obj = ChatRoom.query.filter_by(is_global=True).first()
        if not room_obj:
            return emit("error", {"message": "Room not found"})
        room_name = f"chatroom-{room_obj.id}"
        join_room(room_name)
        history = Message.query.filter_by(chat_room_id=room_obj.id).order_by(Message.created_at).all()
        emit("history", [m.to_dict() for m in history])

    @socketio.on("send_message")
    def handle_send_message(data):
        token = request.cookies.get("access_token")
        if not token:
            return emit("error", {"message": "Not authenticated"})
        try:
            decoded = decode_jwt(token)
        except:
            return emit("error", {"message": "Invalid or expired token"})
        user_id = decoded.get("user_id")
        course_id = data.get("course_id")
        content = (data.get("content") or "").strip()
        if not content:
            return emit("error", {"message": "Content required"})
        if course_id:
            allowed = (
                db.session.query(Course)
                .join(Enrolment, Course.degree_id == Enrolment.degree_id)
                .filter(Enrolment.student_id == user_id, Course.id == course_id)
                .first()
            )
            if not allowed:
                return emit("error", {"message": "Forbidden"})
            room_obj = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
        else:
            room_obj = ChatRoom.query.filter_by(is_global=True).first()
        if not room_obj:
            return emit("error", {"message": "Room not found"})
        msg = Message(chat_room_id=room_obj.id, sender_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        emit("new_message", msg.to_dict(), room=f"chatroom-{room_obj.id}")

    @socketio.on("leave")
    def handle_leave(data):
        course_id = data.get("course_id")
        if course_id:
            room_obj = ChatRoom.query.filter_by(course_id=course_id, is_global=False).first()
        else:
            room_obj = ChatRoom.query.filter_by(is_global=True).first()
        if room_obj:
            leave_room(f"chatroom-{room_obj.id}")
