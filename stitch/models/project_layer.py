"""ProjectLayer model for normalized layer storage"""
from stitch.database import db
from datetime import datetime


class ProjectLayer(db.Model):
    """
    Normalized storage for project layers.

    Each row represents one layer in a project's layer stack.
    Layers are ordered by sort_order (0 = bottom).

    Layer types:
        - 'raster': Editable stitch layer
        - 'reference': Read-only reference image layer
    """
    __tablename__ = 'project_layers'

    id = db.Column(db.String(36), primary_key=True)  # Reuses frontend UUID
    project_id = db.Column(db.String(36), nullable=False, index=True)  # Reference to projects.id (no FK)
    layer_type = db.Column(db.String(20), nullable=False)  # 'raster' or 'reference'
    name = db.Column(db.String(255), nullable=False)
    visible = db.Column(db.Boolean, default=True, nullable=False)
    active_for_export = db.Column(db.Boolean, default=True, nullable=False)
    editable = db.Column(db.Boolean, default=True, nullable=False)
    opacity = db.Column(db.Float, nullable=True)  # Reference layers only
    image_url = db.Column(db.String(500), nullable=True)  # URL for reference layer images
    sort_order = db.Column(db.Integer, nullable=False, default=0)  # Layer stacking order (0 = bottom)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProjectLayer {self.name} ({self.layer_type})>'

    def to_dict(self):
        """Convert layer to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'layer_type': self.layer_type,
            'name': self.name,
            'visible': self.visible,
            'active_for_export': self.active_for_export,
            'editable': self.editable,
            'opacity': self.opacity,
            'image_url': self.image_url,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }