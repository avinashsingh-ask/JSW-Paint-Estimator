"""Pydantic models for API responses."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AreaCalculation(BaseModel):
    """Area calculation details."""
    
    total_wall_area: float = Field(..., description="Total wall area in sq ft")
    door_area: float = Field(..., description="Total door area in sq ft")
    window_area: float = Field(..., description="Total window area in sq ft")
    ceiling_area: Optional[float] = Field(default=None, description="Ceiling area in sq ft")
    paintable_area: float = Field(..., description="Paintable area in sq ft")


class ProductQuantity(BaseModel):
    """Product quantity details."""
    
    product_name: str = Field(..., description="Product name")
    product_type: str = Field(..., description="Product type (primer/putty/paint)")
    quantity: float = Field(..., description="Quantity required")
    unit: str = Field(..., description="Unit of measurement (liters/kg)")
    price_per_unit: float = Field(..., description="Price per unit in ₹")
    total_cost: float = Field(..., description="Total cost in ₹")
    coverage_per_unit: float = Field(..., description="Coverage per unit")


class ProductBreakdown(BaseModel):
    """Product-wise breakdown."""
    
    primer: Optional[ProductQuantity] = Field(default=None, description="Primer details")
    putty: Optional[ProductQuantity] = Field(default=None, description="Putty details")
    paint: ProductQuantity = Field(..., description="Paint details")


class CostBreakdown(BaseModel):
    """Cost breakdown."""
    
    primer_cost: float = Field(default=0, description="Primer cost in ₹")
    putty_cost: float = Field(default=0, description="Putty cost in ₹")
    paint_cost: float = Field(..., description="Paint cost in ₹")
    total_cost: float = Field(..., description="Total estimated cost in ₹")


class EstimationOutput(BaseModel):
    """Main estimation output model."""
    
    area_calculation: AreaCalculation = Field(..., description="Area calculation details")
    product_breakdown: ProductBreakdown = Field(..., description="Product-wise breakdown")
    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown")
    
    # Metadata
    paint_type: str = Field(..., description="Paint type used")
    num_coats: int = Field(..., description="Number of coats")
    
    # Quick summary
    summary: Dict[str, Any] = Field(
        ...,
        description="Quick summary with key metrics"
    )


class RoomEstimationOutput(BaseModel):
    """Output for individual room estimation."""
    
    room_name: Optional[str] = Field(default=None, description="Room identifier")
    room_type: Optional[str] = Field(default=None, description="Room type")
    estimation: EstimationOutput = Field(..., description="Estimation details")


class MultiRoomEstimationOutput(BaseModel):
    """Output for multiple rooms estimation."""
    
    rooms: List[RoomEstimationOutput] = Field(..., description="Individual room estimations")
    total_summary: Dict[str, Any] = Field(..., description="Aggregated summary")
    total_cost: float = Field(..., description="Total cost for all rooms in ₹")
    total_paint_required: float = Field(..., description="Total paint required in liters")
    total_paintable_area: float = Field(..., description="Total paintable area in sq ft")


class CVEstimationOutput(EstimationOutput):
    """Output for CV-based estimation with detection results."""
    
    detection_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Object detection results"
    )
    image_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Image analysis metadata"
    )


class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    models_loaded: Dict[str, bool] = Field(
        default={},
        description="Status of loaded ML models"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = Field(default=False, description="Success flag")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
