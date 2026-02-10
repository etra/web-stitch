"""Request/response schemas for the vote resource."""
from pydantic import BaseModel, field_validator


class VoteRequest(BaseModel):
    """Request body for POST /api/projects/<id>/vote."""
    value: int

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v not in (1, -1):
            raise ValueError('value must be 1 or -1')
        return v


class VoteResponse(BaseModel):
    """Response for vote endpoints."""
    vote_score: int
    user_vote: int
