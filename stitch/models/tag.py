"""Tag model for categorizing projects."""
from datetime import datetime
from stitch.database import db


class Tag(db.Model):
    """
    Tag for categorizing projects.

    Tags are normalized: lowercase, trimmed, no special characters, max 50 chars.
    Tags are unique by name and shared across all projects.
    """
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Tag {self.name}>'
