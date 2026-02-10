"""ProjectVote model for storing user votes on projects."""
from stitch.database import db
from datetime import datetime


class ProjectVote(db.Model):
    """
    Stores a single user's vote on a project.

    Each user may cast one vote per project (+1 or -1).
    The unique constraint ensures one vote per user per project.
    No database foreign keys (consistent with project pattern).
    """
    __tablename__ = 'project_votes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    value = db.Column(db.SmallInteger, nullable=False)  # +1 or -1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_vote_user'),
    )

    def __repr__(self):
        return f'<ProjectVote project={self.project_id} user={self.user_id} value={self.value}>'
