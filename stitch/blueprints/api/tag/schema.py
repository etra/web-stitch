"""Response schemas for the tag resource."""
from pydantic import BaseModel


class TagResponse(BaseModel):
    """Single tag entry."""
    id: int
    name: str


class TagsListResponse(BaseModel):
    """Response schema for GET /api/tags."""
    tags: list[TagResponse]
