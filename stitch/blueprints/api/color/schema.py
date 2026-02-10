"""Response schemas for the color resource."""
from pydantic import BaseModel


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
    colors: list[ColorResponse]


class VendorColorResponse(BaseModel):
    """Single color entry in vendor-specific API response."""
    id: int
    vendor: str
    code: str
    name: str
    hex: str
    is_default: bool


class VendorColorsListResponse(BaseModel):
    """Response schema for GET /api/colors/vendors/<vendor>."""
    colors: list[VendorColorResponse]


class VendorResponse(BaseModel):
    """Single vendor entry in API response."""
    key: str
    name: str
    full_name: str
    description: str
    type: str
    color_count: int


class VendorsListResponse(BaseModel):
    """Response schema for GET /api/colors/vendors."""
    vendors: list[VendorResponse]
