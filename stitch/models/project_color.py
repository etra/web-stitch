"""ProjectColor model for storing colors used in a project."""
from stitch.database import db
import uuid


class ProjectColor(db.Model):
    """
    A color assigned to a project's palette.

    Links a project to a color from the catalog (colors table)
    with a chart symbol for pattern display.

    Fields:
        id:         UUID primary key.
        project_id: Reference to projects.id (no DB FK).
        color_id:   Reference to colors.id (no DB FK).
        symbol:     Chart symbol for pattern display (e.g. 'A', 'B').
        sort_order: Display ordering within the project palette (0-based).
    """
    __tablename__ = 'project_colors'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), nullable=False, index=True)
    color_id = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    color = db.relationship('Color',
         primaryjoin='ProjectColor.color_id==Color.id',
         foreign_keys='[ProjectColor.color_id]',
         uselist=False)

    def __repr__(self):
        return f'<ProjectColor project={self.project_id} color={self.color_id}>'
