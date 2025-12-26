"""Pydantic models for manual estimation (Scenario 1)."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class RoomInput(BaseModel):
    """Input model for a single room."""
    
    length: float = Field(..., gt=0, description="Room length in feet")
    width: float = Field(..., gt=0, description="Room width in feet")
    height: float = Field(..., gt=0, description="Room/ceiling height in feet")
    num_doors: int = Field(default=0, ge=0, description="Number of doors")
    num_windows: int = Field(default=0, ge=0, description="Number of windows")
    
    # Optional custom door/window dimensions
    door_height: Optional[float] = Field(default=7.0, gt=0, description="Door height in feet")
    door_width: Optional[float] = Field(default=3.0, gt=0, description="Door width in feet")
    window_height: Optional[float] = Field(default=4.0, gt=0, description="Window height in feet")
    window_width: Optional[float] = Field(default=3.0, gt=0, description="Window width in feet")
    
    @field_validator('num_doors', 'num_windows')
    @classmethod
    def validate_count(cls, v: int) -> int:
        """Validate door/window count is reasonable."""
        if v > 20:
            raise ValueError("Number of doors/windows seems unusually high (max 20)")
        return v


class ManualEstimationRequest(BaseModel):
    """Request model for manual paint estimation (Scenario 1)."""
    
    room: RoomInput = Field(..., description="Room dimensions and details")
    paint_type: str = Field(..., description="Paint type: 'interior' or 'exterior'")
    paint_product: Optional[str] = Field(
        default=None,
        description="Specific paint product (e.g., 'premium_emulsion'). If not provided, default will be used."
    )
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
    
    @field_validator('num_coats')
    @classmethod
    def validate_num_coats(cls, v: int) -> int:
        """Validate number of coats."""
        if v < 1:
            raise ValueError("num_coats must be at least 1")
        if v > 5:
            raise ValueError("num_coats cannot exceed 5")
        return v


class MultiRoomEstimationRequest(BaseModel):
    """Request model for multiple rooms estimation."""
    
    rooms: list[RoomInput] = Field(..., min_length=1, description="List of rooms")
    paint_type: str = Field(..., description="Paint type: 'interior' or 'exterior'")
    paint_product: Optional[str] = Field(default=None, description="Specific paint product")
    num_coats: int = Field(default=2, ge=1, le=5, description="Number of paint coats")
    include_ceilings: bool = Field(default=False, description="Whether to paint ceilings")
    
    @field_validator('paint_type')
    @classmethod
    def validate_paint_type(cls, v: str) -> str:
        """Validate paint type."""
        v = v.lower()
        if v not in ['interior', 'exterior']:
            raise ValueError("paint_type must be 'interior' or 'exterior'")
        return v
