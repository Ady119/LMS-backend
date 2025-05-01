# routes/chat.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import db, Message, Enrolment

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/messages/<int:course_id>', methods=['GET'])
def get_messages(course_id):
    verify_jwt_in_request(locations=['cookies'])
    user_id = get_jwt_identity()
    enrolled = db.session.query(Enrolment) \
        .filter_by(student_id=user_id, course_id=course_id) \
        .first()
    if not enrolled:
        return jsonify({'message': 'Forbidden'}), 403
    msgs = Message.query \
        .filter_by(course_id=course_id) \
        .order_by(Message.created_at) \
        .all()
    return jsonify([m.to_dict() for m in msgs]), 200

@chat_bp.route('/messages', methods=['POST'])
def post_message():
    verify_jwt_in_request(locations=['cookies'])
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    course_id = data.get('course_id')
    content = (data.get('content') or '').strip()
    if not course_id or not content:
        return jsonify({'message': 'course_id and content required'}), 400
    enrolled = db.session.query(Enrolment) \
        .filter_by(student_id=user_id, course_id=course_id) \
        .first()
    if not enrolled:
        return jsonify({'message': 'Forbidden'}), 403
    msg = Message(course_id=course_id, sender_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201
