from models import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon_url = db.Column(db.String(255), nullable=True)
    criteria = db.Column(db.String(255), nullable=True)

class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    badge = relationship("Badge")
