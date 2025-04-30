from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Message, Enrolment

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# When you configure JWTManager, make sure it knows to look in cookies:
#   app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
#   app.config["JWT_COOKIE_SECURE"]   = True
#   app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"

@chat_bp.route("/messages", methods=["GET"])
@jwt_required(locations=["cookies"])
def get_messages():
    user_id   = get_jwt_identity()
    course_id = request.args.get("course_id", type=int)
    if not course_id:
        return jsonify({"error": "Missing course_id"}), 400

    # check enrollment
    ok = (
        db.session.query(Enrolment)
        .filter_by(student_id=user_id, course_id=course_id)
        .first()
    )
    if not ok:
        return jsonify({"error": "Forbidden"}), 403

    msgs = (
        Message.query
        .filter_by(course_id=course_id)
        .order_by(Message.created_at)
        .all()
    )
    return jsonify([m.to_dict() for m in msgs])


@chat_bp.route("/messages", methods=["POST"])
@jwt_required(locations=["cookies"])
def post_message():
    user_id = get_jwt_identity()
    data    = request.get_json() or {}
    course_id = data.get("course_id")
    content   = data.get("content", "").strip()

    if not course_id or not content:
        return jsonify({"error": "course_id and content required"}), 400

    # check enrollment
    ok = (
        db.session.query(Enrolment)
        .filter_by(student_id=user_id, course_id=course_id)
        .first()
    )
    if not ok:
        return jsonify({"error": "Forbidden"}), 403

    msg = Message(course_id=course_id, sender_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()

    return jsonify(msg.to_dict()), 201
