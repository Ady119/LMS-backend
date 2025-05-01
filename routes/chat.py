from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Course, Message, ChatRoom, Enrolment, LecturerCourse

chat_bp = Blueprint('chat_bp', __name__)

def _message_with_sender(m: Message):
    user = User.query.get(m.sender_id)
    return { **m.to_dict(), "sender_name": user.username if user else None }

@chat_bp.route('/rooms', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_rooms():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    rooms = []

    # global
    global_room = ChatRoom.query.filter_by(is_global=True).first()
    if global_room:
        rooms.append({'id': global_room.id, 'name': 'Global', 'is_global': True})

    if user.role == 'student':
        qs = Enrolment.query.filter_by(student_id=user_id).all()
        course_ids = [e.course_id for e in qs]
    elif user.role == 'lecturer':
        qs = LecturerCourse.query.filter_by(lecturer_id=user_id).all()
        course_ids = [lc.course_id for lc in qs]
    else:
        course_ids = []

    for cid in course_ids:
        room = ChatRoom.query.filter_by(course_id=cid, is_global=False).first()
        if room:
            rooms.append({'id': room.id, 'name': f'Course {cid}', 'is_global': False})

    return jsonify(rooms), 200

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_room_messages(room_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if not room.is_global:
        allowed = False
        if user.role == 'student':
            allowed = Enrolment.query.filter_by(student_id=user_id, course_id=room.course_id).first()
        elif user.role == 'lecturer':
            allowed = LecturerCourse.query.filter_by(lecturer_id=user_id, course_id=room.course_id).first()
        if not allowed:
            return jsonify({'error': 'Forbidden'}), 403
    msgs = Message.query.filter_by(chat_room_id=room_id).order_by(Message.created_at).all()
    return jsonify([_message_with_sender(m) for m in msgs]), 200

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['POST'])
@jwt_required(locations=['cookies'])
def post_message(room_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Content required'}), 400
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if not room.is_global:
        allowed = False
        if user.role == 'student':
            allowed = Enrolment.query.filter_by(student_id=user_id, course_id=room.course_id).first()
        elif user.role == 'lecturer':
            allowed = LecturerCourse.query.filter_by(lecturer_id=user_id, course_id=room.course_id).first()
        if not allowed:
            return jsonify({'error': 'Forbidden'}), 403
    msg = Message(chat_room_id=room_id, sender_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify(_message_with_sender(msg)), 201
