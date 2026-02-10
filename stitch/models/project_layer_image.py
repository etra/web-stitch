"""ProjectLayerImage model for storing base64 reference images."""
from stitch.database import db


class ProjectLayerImage(db.Model):
    """
    Base64 reference image for a project layer, stored separately to
    avoid loading heavy data when only layer metadata is needed.

    One row per layer. The data column holds a raw base64 data URI string.

    Fields:
        layer_id: Reference to project_layers.id (no DB FK). Primary key.
        data:     Base64 data URI string (Text).
    """
    __tablename__ = 'project_layer_images'

    layer_id = db.Column(db.String(36), primary_key=True)
    data = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ProjectLayerImage layer={self.layer_id}>'
