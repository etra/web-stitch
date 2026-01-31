"""Project model for storing cross-stitch patterns"""
from stitch.database import db
from datetime import datetime
from enum import IntEnum
import uuid


class ProjectStatus(IntEnum):
    """Project visibility/status values"""
    DELETED = -1
    DEFAULT = 0
    PUBLIC = 1
    PRIVATE = 2


class Project(db.Model):
    """Project model storing cross-stitch patterns"""
    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)  # Reference to users.id (no FK)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    cloth_color = db.Column(db.String(7), default='#ffffff')
    status = db.Column(db.SmallInteger, default=ProjectStatus.DEFAULT, nullable=False, index=True)
    state = db.Column(db.JSON, nullable=False)  # Full project state (palette, layers, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user (no database FK constraint)
    user = db.relationship('User',
                          primaryjoin='Project.user_id==User.id',
                          foreign_keys='[Project.user_id]',
                          back_populates='projects')

    def __repr__(self):
        return f'<Project {self.name}>'

    def to_dict(self):
        """Convert project to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'width': self.width,
            'height': self.height,
            'cloth_color': self.cloth_color,
            'status': self.status,
            'state': self.state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_deleted(self) -> bool:
        """Check if project is soft-deleted"""
        return self.status == ProjectStatus.DELETED

    @property
    def is_public(self) -> bool:
        """Check if project is public"""
        return self.status == ProjectStatus.PUBLIC
