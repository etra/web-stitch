"""ProjectLayerCells model and data schemas for layer cell data."""
from pydantic import BaseModel, RootModel
from stitch.database import db


class CellStitch(BaseModel):
    """
    A single stitch within a cell.

    Fields:
        color:  ID of the ProjectColor entry (references project_colors.id).
        stitch: Stitch type key (e.g. 'full', 'half-slash', 'french-knot').
    """
    color: str
    stitch: str


# Keep backward-compatible alias
Cell = CellStitch


class Cells(RootModel[dict[str, list[CellStitch]]]):
    """
    Sparse grid of cells. Keys are "x,y" coordinate strings.
    Each cell contains a list of stitches (supports multiple stitches per cell).
    """
    pass


class ProjectLayerCells(db.Model):
    """
    Cell data for a project layer, stored separately to avoid loading
    heavy JSON when only layer metadata is needed.

    One row per layer. The data column holds a sparse dict of cells
    keyed by "x,y" coordinate strings.

    Fields:
        layer_id: Reference to project_layers.id (no DB FK). Primary key.
        data:     Sparse cell dict (JSON).
    """
    __tablename__ = 'project_layer_cells'

    layer_id = db.Column(db.String(36), primary_key=True)
    data = db.Column(db.JSON, nullable=False, default=dict)

    @property
    def cells(self) -> Cells:
        """Get cells as a validated Cells object."""
        raw = self.data or {}
        return Cells.model_validate(raw)

    @cells.setter
    def cells(self, value: Cells) -> None:
        """Set cells from a Cells object."""
        self.data = value.model_dump()

    def __repr__(self):
        return f'<ProjectLayerCells layer={self.layer_id}>'
