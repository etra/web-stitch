from stitch.database import db
from datetime import datetime
import uuid


class User(db.Model):
    """User model with email-only authentication (MVP)"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (no database FK constraints)
    projects = db.relationship('Project',
                              primaryjoin='User.id==Project.user_id',
                              foreign_keys='[Project.user_id]',
                              back_populates='user',
                              lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'
