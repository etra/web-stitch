"""ProjectTag junction model linking projects to tags."""
from stitch.database import db


class ProjectTag(db.Model):
    """
    Junction table linking projects to tags (many-to-many).

    Composite primary key (project_id, tag_id).
    No database foreign keys (consistent with project pattern).
    """
    __tablename__ = 'project_tags'

    project_id = db.Column(db.String(36), primary_key=True)
    tag_id = db.Column(db.Integer, primary_key=True)
