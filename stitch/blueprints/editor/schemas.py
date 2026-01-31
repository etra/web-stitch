"""Request/response schemas for editor endpoints."""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class SaveStateRequest(BaseModel):
    """Schema for saving project state."""
    state: Dict[str, Any]


class SaveStateResponse(BaseModel):
    """Schema for save state response."""
    success: bool
    message: str


class ProjectStateResponse(BaseModel):
    """Schema for project state response."""
    id: str
    name: str
    description: Optional[str]
    width: int
    height: int
    clothColor: str
    state: Dict[str, Any]
