"""Request/response schemas for projects endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


class ProjectCreateRequest(BaseModel):
    """Schema for project creation form."""
    name: str = Field(..., min_length=1, max_length=255)
    width: int = Field(..., ge=1, le=1000)
    height: int = Field(..., ge=1, le=1000)
    cloth_color: str = Field(default='#ffffff', pattern=r'^#[0-9a-fA-F]{6}$')


class ProjectEditRequest(BaseModel):
    """Schema for project edit form."""
    name: str = Field(..., min_length=1, max_length=255)
    width: int = Field(..., ge=1, le=1000)
    height: int = Field(..., ge=1, le=1000)
    cloth_color: str = Field(default='#ffffff', pattern=r'^#[0-9a-fA-F]{6}$')


class WizardSetupRequest(BaseModel):
    """Schema for wizard setup step."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    width: int = Field(..., ge=10, le=1000)
    height: int = Field(..., ge=10, le=1000)


class WizardVendorRequest(BaseModel):
    """Schema for wizard vendor selection step."""
    vendor: str = Field(..., pattern=r'^(dmc|hama|artkal|nabbi)$')
