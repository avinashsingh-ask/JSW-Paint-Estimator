"""Pydantic models for CV-based estimation (Scenario 2)."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from fastapi import UploadFile


class ReferenceObject(BaseModel):
    """Reference object for scale calibration."""
    
    object_type: Literal["door", "window", "custom"] = Field(
        default="door",
        description="Type of reference object"
    )
    real_height: Optional[float] = Field(
        default=None,
        gt=0,
        description="Real height in feet (required for custom objects)"
    )
    real_width: Optional[float] = Field(
        default=None,
        gt=0,
        description="Real width in feet (required for custom objects)"
    )


class CVRoomInput(BaseModel):
    """Input model for CV-based room estimation."""
    
    room_type: Literal["bedroom", "hall", "kitchen", "bathroom", "other"] = Field(
        ...,
        description="Type of room"
    )
    
    # Optional manual overrides
    length: Optional[float] = Field(default=None, gt=0, description="Manual room length override in feet")
    width: Optional[float] = Field(default=None, gt=0, description="Manual room width override in feet")
    height: Optional[float] = Field(default=None, gt=0, description="Manual room height override in feet")
    
    reference_object: Optional[ReferenceObject] = Field(
        default=None,
        description="Reference object for scale calibration"
    )
    
    @field_validator('length', 'width', 'height')
    @classmethod
    def validate_dimensions(cls, v: Optional[float]) -> Optional[float]:
        """Validate dimensions if provided."""
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("Dimension must be between 0 and 100 feet")
        return v


class CVEstimationRequest(BaseModel):
    """Request model for CV-based estimation (Scenario 2)."""
    
    # Note: image upload will be handled separately in the API endpoint
    room_info: CVRoomInput = Field(..., description="Room information")
    paint_type: str = Field(default="interior", description="Paint type: 'interior' or 'exterior'")
    paint_product: Optional[str] = Field(default=None, description="Specific paint product")
    num_coats: int = Field(default=2, ge=1, le=5, description="Number of paint coats")
    include_ceiling: bool = Field(default=False, description="Whether to paint ceiling")
    
    @field_validator('paint_type')
    @classmethod
    def validate_paint_type(cls, v: str) -> str:
        """Validate paint type."""
        v = v.lower()
        if v not in ['interior', 'exterior']:
            raise ValueError("paint_type must be 'interior' or 'exterior'")
        return v


class MultiRoomCVRequest(BaseModel):
    """Request model for multiple rooms CV estimation."""
    
    rooms: list[CVRoomInput] = Field(..., min_length=1, description="List of rooms")
    exterior_area: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional exterior area in sq ft"
    )
    num_coats: int = Field(default=2, ge=1, le=5, description="Number of paint coats")
    include_ceilings: bool = Field(default=False, description="Whether to paint ceilings")


class DetectionResult(BaseModel):
    """Model for object detection results."""
    
    object_type: str = Field(..., description="Type of detected object (door/window)")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence score")
    bounding_box: dict = Field(..., description="Bounding box coordinates {x, y, w, h}")
    

class RoomDetectionResult(BaseModel):
    """Model for room detection results."""
    
    room_type: str = Field(..., description="Type of room")
    detected_doors: int = Field(default=0, description="Number of doors detected")
    detected_windows: int = Field(default=0, description="Number of windows detected")
    detections: list[DetectionResult] = Field(default=[], description="Individual detection results")
    estimated_dimensions: Optional[dict] = Field(
        default=None,
        description="Estimated room dimensions {length, width, height}"
    )


class VideoEstimationInput(BaseModel):
    """Input model for video-based room estimation."""
    
    room_type: Literal["bedroom", "hall", "kitchen", "bathroom", "other"] = Field(
        ...,
        description="Type of room"
    )
    
    # Optional manual overrides
    length: Optional[float] = Field(default=None, gt=0, description="Manual room length override in feet")
    width: Optional[float] = Field(default=None, gt=0, description="Manual room width override in feet")
    height: Optional[float] = Field(default=None, gt=0, description="Manual room height override in feet")
    
    @field_validator('length', 'width', 'height')
    @classmethod
    def validate_dimensions(cls, v: Optional[float]) -> Optional[float]:
        """Validate dimensions if provided."""
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("Dimension must be between 0 and 100 feet")
        return v


class FrameAnalysis(BaseModel):
    """Individual frame detection results."""
    
    frame_number: int = Field(..., description="Frame number")
    detections: list = Field(default=[], description="Objects detected in frame")
    counts: dict = Field(default={}, description="Object counts in frame")
    dimensions: dict = Field(default={}, description="Estimated dimensions from frame")


class VideoMetadata(BaseModel):
    """Video file metadata."""
    
    duration: float = Field(..., description="Video duration in seconds")
    fps: float = Field(..., description="Video frames per second")
    frame_count: int = Field(..., description="Total frames in video")
    resolution: dict = Field(..., description="Video resolution {width, height}")
    file_size: int = Field(..., description="File size in bytes")


class VideoEstimationOutput(BaseModel):
    """Output model for video-based estimation results."""
    
    metadata: dict = Field(..., description="Video metadata")
    frame_count: int = Field(..., description="Number of frames analyzed")
    aggregated_dimensions: dict = Field(..., description="Aggregated room dimensions")
    aggregated_counts: dict = Field(..., description="Aggregated object counts")
    detection_confidence: dict = Field(..., description="Confidence metrics")
    detections_summary: dict = Field(..., description="Summary of all detections")
    frame_results: Optional[list[FrameAnalysis]] = Field(
        default=None,
        description="Individual frame analysis results (optional)"
    )

