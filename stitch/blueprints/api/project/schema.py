"""Response schemas for the project resource."""
from typing import ClassVar, Optional

from pydantic import BaseModel, field_validator

from stitch.models.project_layer_cells import CellStitch
from stitch.models.project_layer_paths import Path


class ProjectResponse(BaseModel):
    """Project metadata in API response (used in list endpoints)."""
    id: str
    name: str
    description: Optional[str]
    width: int
    height: int
    clothColor: str


class ProjectsListResponse(BaseModel):
    """Response schema for GET /api/projects."""
    projects: list[ProjectResponse]


class ProjectColorResponse(BaseModel):
    """Single project color entry."""
    id: str
    colorId: int
    symbol: str
    vendor: str
    code: str
    name: str
    rgbHex: str

    # {'id': c.id, 'colorId': c.color_id, 'symbol': c.symbol, 'vendor': c.color.vendor, 'code': c.color.code, 'name': c.color.name, 'rgbHex': c.color.hex}


class LayerResponse(BaseModel):
    """Single layer entry in full project response."""
    id: str
    type: str
    name: str
    visible: bool
    activeForExport: bool
    editable: bool
    opacity: Optional[float] = None
    referenceImageData: Optional[str] = None
    sortOrder: int
    offsetX: int = 0
    offsetY: int = 0
    cells: dict[str, list[CellStitch]]
    paths: list[Path]



class ProjectPropertiesResponse(BaseModel):
    """Project-level editor properties."""
    majorGridInterval: int
    showGridNumbers: bool
    defaultStitchType: str

class CanvasResponse(BaseModel):
    """Canvas settings for the project."""
    width: int
    height: int
    color: str


class ProjectLimitsResponse(BaseModel):
    """Project-level limits."""
    maxPaletteColors: int


class FullProjectResponse(BaseModel):
    """Full project data including state."""
    id: str
    name: str
    description: Optional[str]
    width: int
    height: int
    clothColor: str
    status: int
    activeLayerId: Optional[str]
    createdAt: Optional[str]
    updatedAt: Optional[str]
    colors: list[ProjectColorResponse]
    layers: list[LayerResponse]
    properties: ProjectPropertiesResponse
    canvas: CanvasResponse
    limits: ProjectLimitsResponse


class FullProjectDataResponse(BaseModel):
    """Response schema for GET /api/projects/<project_id>."""
    project: FullProjectResponse


class ProjectLayersResponse(BaseModel):
    """Response schema for GET /api/projects/<project_id>/layers."""
    layers: list[LayerResponse]


# --- Request schemas for POST /api/projects/<project_id> ---

class SaveProjectColorRequest(BaseModel):
    """Color entry in save request."""
    id: str
    colorId: int
    symbol: str
    name: str
    rgbHex: str
    vendor: str
    code: str


class SaveProjectLayerRequest(BaseModel):
    """Layer entry in save request."""
    # Max size for referenceImageData: 5 MB of base64 (~3.75 MB original image)
    MAX_REFERENCE_IMAGE_BYTES: ClassVar[int] = 5 * 1024 * 1024

    id: str
    type: str
    name: str
    visible: bool
    activeForExport: bool
    editable: bool
    opacity: Optional[float] = None
    referenceImageData: Optional[str] = None
    sortOrder: int
    offsetX: int = 0
    offsetY: int = 0
    cells: dict[str, list[CellStitch]]
    paths: list[Path]

    @field_validator('referenceImageData')
    @classmethod
    def validate_reference_image_size(cls, v):
        if v is not None and len(v) > cls.MAX_REFERENCE_IMAGE_BYTES:
            max_mb = cls.MAX_REFERENCE_IMAGE_BYTES / (1024 * 1024)
            raise ValueError(f'referenceImageData exceeds maximum size of {max_mb:.0f} MB')
        return v


class SaveProjectPropertiesRequest(BaseModel):
    """Properties in save request."""
    majorGridInterval: int
    showGridNumbers: bool
    defaultStitchType: str


class SaveProjectRequest(BaseModel):
    """Request schema for POST /api/projects/<project_id>."""
    activeLayerId: str
    colors: list[SaveProjectColorRequest]
    layers: list[SaveProjectLayerRequest]
    properties: SaveProjectPropertiesRequest


class SaveProjectResponse(BaseModel):
    """Response schema for POST /api/projects/<project_id>."""
    success: bool
    savedAt: str


# --- Schemas for image layer endpoints ---

class ConvertToStitchesRequest(BaseModel):
    """Request schema for POST /api/projects/<id>/layers/<id>/convert-to-stitches."""
    maxColors: int
    useExistingColorsOnly: bool


class NewColorResponse(BaseModel):
    """A new color generated from image conversion."""
    id: str
    colorId: int
    symbol: str
    name: str
    rgbHex: str
    vendor: str
    code: str


class ReferenceImageResponse(BaseModel):
    """Response schema for POST /api/projects/<id>/layers/from-image-reference."""
    imageUrl: str
    originalWidth: int
    originalHeight: int


class ImageToStitchesResponse(BaseModel):
    """Response schema for POST /api/projects/<id>/layers/from-image-stitches."""
    layer: LayerResponse
    newColors: list[NewColorResponse]


# --- Palette management schemas ---

class AddPaletteColorsRequest(BaseModel):
    """Request schema for POST /api/projects/<id>/palette/colors."""
    colorIds: list[int]


class AddPaletteColorsResponse(BaseModel):
    """Response schema for POST /api/projects/<id>/palette/colors."""
    colors: list[ProjectColorResponse]
    paletteCount: int
    maxPaletteColors: int


class RemovePaletteColorsRequest(BaseModel):
    """Request schema for POST /api/projects/<id>/palette/colors/remove."""
    colorIds: list[str]


class RemovePaletteColorsResponse(BaseModel):
    """Response schema for POST /api/projects/<id>/palette/colors/remove."""
    success: bool


class MergePairRequest(BaseModel):
    """A single merge pair: source color gets replaced by target color."""
    sourceColorId: str
    targetColorId: str


class MergePaletteColorsRequest(BaseModel):
    """Request schema for POST /api/projects/<id>/palette/merge."""
    merges: list[MergePairRequest]


class MergePaletteColorsResponse(BaseModel):
    """Response schema for POST /api/projects/<id>/palette/merge."""
    success: bool
