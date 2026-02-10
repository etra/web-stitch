"""ProjectLayerPaths model and data schemas for layer path data."""
from pydantic import BaseModel, Field, RootModel
from stitch.database import db


class Path(BaseModel):
    """
    A single path (e.g. backstitch line) between two grid points.

    Fields:
        startX: Start X grid coordinate.
        startY: Start Y grid coordinate.
        endX:   End X grid coordinate.
        endY:   End Y grid coordinate.
        color:  ID of the ProjectColor entry (references project_colors.id).
        stitch: Stitch type key (e.g. 'backstitch').
    """
    startX: int = Field(..., ge=0)
    startY: int = Field(..., ge=0)
    endX: int = Field(..., ge=0)
    endY: int = Field(..., ge=0)
    color: str
    stitch: str


class Paths(RootModel[list[Path]]):
    """List of path objects for a layer."""
    pass


class ProjectLayerPaths(db.Model):
    """
    Path data for a project layer, stored separately to avoid loading
    heavy JSON when only layer metadata is needed.

    One row per layer. The data column holds an array of paths.

    Fields:
        layer_id: Reference to project_layers.id (no DB FK). Primary key.
        data:     Array of path objects (JSON).
    """
    __tablename__ = 'project_layer_paths'

    layer_id = db.Column(db.String(36), primary_key=True)
    data = db.Column(db.JSON, nullable=False, default=list)

    @property
    def paths(self) -> Paths:
        """Get paths as a validated Paths object."""
        return Paths.model_validate(self.data or [])

    @paths.setter
    def paths(self, value: Paths) -> None:
        """Set paths from a Paths object."""
        self.data = value.model_dump()

    def __repr__(self):
        return f'<ProjectLayerPaths layer={self.layer_id}>'
