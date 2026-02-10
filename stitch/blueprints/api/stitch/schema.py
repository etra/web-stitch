"""Response schemas for the stitch resource."""
from pydantic import BaseModel


class StitchResponse(BaseModel):
    """Single stitch type entry in API response."""
    type: str
    name: str
    category: str
    icon: str
    sort_order: int
    render_mode: str
    occupancy: list[str]
    path_data: list | None = None


class StitchesListResponse(BaseModel):
    """Response model for GET /api/stitches."""
    stitches: list[StitchResponse]
