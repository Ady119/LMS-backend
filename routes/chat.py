from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Message, ChatRoom, Enrolment

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/rooms', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_rooms():
    """List available chat rooms: the global room plus any course rooms the user is enrolled in."""
    user_id = get_jwt_identity()
    rooms = []

    # Global room
    global_room = ChatRoom.query.filter_by(is_global=True).first()
    if global_room:
        rooms.append({
            'id': global_room.id,
            'name': 'Global',
            'is_global': True
        })

    enrollments = db.session.query(Enrolment).filter_by(student_id=user_id).all()
    for e in enrollments:
        room = ChatRoom.query.filter_by(course_id=e.course_id, is_global=False).first()
        if room:
            rooms.append({
                'id': room.id,
                'name': f'Course {e.course_id}',
                'is_global': False
            })

    return jsonify(rooms), 200

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_room_messages(room_id):
    """Fetch message history for a given room."""
    user_id = get_jwt_identity()
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    if not room.is_global:
        enrolled = db.session.query(Enrolment).filter_by(
            student_id=user_id,
            course_id=room.course_id
        ).first()
        if not enrolled:
            return jsonify({'error': 'Forbidden'}), 403

    messages = Message.query.filter_by(chat_room_id=room_id).order_by(Message.created_at).all()
    return jsonify([m.to_dict() for m in messages]), 200

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['POST'])
@jwt_required(locations=['cookies'])
def post_message(room_id):
    """Post a new message to the specified room."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Content required'}), 400

    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    if not room.is_global:
        enrolled = db.session.query(Enrolment).filter_by(
            student_id=user_id,
            course_id=room.course_id
        ).first()
        if not enrolled:
            return jsonify({'error': 'Forbidden'}), 403

    msg = Message(chat_room_id=room_id, sender_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201
