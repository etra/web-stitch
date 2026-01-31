"""Request/response schemas for API endpoints."""
from pydantic import BaseModel
from typing import List


class ColorResponse(BaseModel):
    """Single color entry in API response."""
    id: str
    vendor: str
    code: str
    name: str
    hex: str
    text: str


class ColorsListResponse(BaseModel):
    """Response schema for GET /api/colors."""
    colors: List[ColorResponse]
