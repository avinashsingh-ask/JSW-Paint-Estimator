"""Pydantic models for floor plan analysis."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class DimensionData(BaseModel):
    """Floor dimension data."""
    length: float = Field(..., description="Room length in feet")
    width: float = Field(..., description="Room width in feet")
    raw_text: str = Field(..., description="Original text from floor plan")


class RoomData(BaseModel):
    """Individual room analysis result."""
    name: str = Field(..., description="Room name/label")
    dimensions: DimensionData = Field(..., description="Room dimensions")
    floor_area: float = Field(..., description="Floor area in square feet")
    paintable_area: float = Field(..., description="Paintable wall area in square feet")
    num_doors: int = Field(..., description="Estimated number of doors")
    num_windows: int = Field(..., description="Estimated number of windows")
    paint_required_liters: float = Field(..., description="Paint required in liters")
    cost: float = Field(..., description="Total cost in rupees")
    confidence: float = Field(..., description="OCR confidence score (0-100)")


class OCRMetadata(BaseModel):
    """OCR extraction metadata."""
    dimensions_found: int = Field(..., description="Number of dimensions extracted")
    room_labels_found: int = Field(..., description="Number of room labels found")
    text_regions: int = Field(..., description="Total text regions detected")


class FloorPlanResult(BaseModel):
    """Complete floor plan analysis result."""
    success: bool = Field(..., description="Whether processing was successful")
    rooms: List[RoomData] = Field(..., description="List of analyzed rooms")
    total_rooms: int = Field(..., description="Total number of rooms")
    total_floor_area: float = Field(..., description="Total floor area in square feet")
    total_paintable_area: float = Field(..., description="Total paintable area in square feet")
    total_paint_required_liters: float = Field(..., description="Total paint required in liters")
    total_cost: float = Field(..., description="Total cost in rupees")
    ocr_metadata: OCRMetadata = Field(..., description="OCR extraction metadata")


class FloorPlanInput(BaseModel):
    """Floor plan analysis input parameters."""
    ceiling_height: float = Field(default=10.0, description="Ceiling height in feet", ge=7, le=20)
    paint_type: str = Field(default="interior", description="Paint type (interior/exterior)")
    num_coats: int = Field(default=2, description="Number of coats", ge=1, le=5)
    include_ceiling: bool = Field(default=False, description="Whether to include ceiling painting")
