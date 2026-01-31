"""Request/response schemas for images endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List


class ProcessAjaxRequest(BaseModel):
    """Schema for AJAX image processing preview."""
    filename: str
    width: int = Field(..., ge=10, le=500)
    height: int = Field(..., ge=10, le=500)
    colors: int = Field(..., ge=2, le=100)


class PrepareRequest(BaseModel):
    """Schema for image preparation form."""
    width: int = Field(..., ge=10, le=500)
    height: int = Field(..., ge=10, le=500)
    colors: int = Field(default=20, ge=2, le=100)


class CreateProjectRequest(BaseModel):
    """Schema for project creation from processed image."""
    name: str = Field(..., min_length=1, max_length=255)


class ColorPreview(BaseModel):
    """Schema for a color in preview palette."""
    id: str
    rgbHex: str
    name: str
    symbol: str
    count: Optional[int] = None


class ProcessPreviewResponse(BaseModel):
    """Schema for AJAX processing preview response."""
    success: bool
    width: int
    height: int
    num_colors: int
    original: str  # Base64 image
    processed: str  # Base64 image
    edges: str  # Base64 image
    palette: List[ColorPreview]
