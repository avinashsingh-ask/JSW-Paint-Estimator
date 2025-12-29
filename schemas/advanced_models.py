"""Manual fallback and learning loop schema updates."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class ManualInputRequest(BaseModel):
    """Request for manual user input when confidence is low."""
    
    needs_manual_input: bool = Field(description="Whether manual input is needed")
    confidence_score: float = Field(description="Current confidence score")
    reason: str = Field(description="Why manual input is needed")
    requested_measurements: List[str] = Field(
        description="List of measurements to request (e.g., ['ceiling_height', 'door_height'])"
    )
    current_estimates: Dict[str, float] = Field(description="Current estimated values")
    
    class Config:
        json_schema_extra = {
            "example": {
                "needs_manual_input": True,
                "confidence_score": 0.35,
                "reason": "No reliable reference objects detected",
                "requested_measurements": ["ceiling_height"],
                "current_estimates": {
                    "length": 12.5,
                    "width": 10.3,
                    "height": 10.0
                }
            }
        }


class LearningDataPoint(BaseModel):
    """Single data point for learning loop."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    estimation_mode: str = Field(description="video/image/manual/blueprint")
    
    # Detected data
    detected_objects: List[Dict[str, Any]] = Field(description="Objects detected")
    reference_objects_used: List[str] = Field(description="Which objects were used for scale")
    
    # Final measurements
    final_dimensions: Dict[str, float] = Field(description="Final room dimensions")
    confidence_scores: Dict[str, float] = Field(description="Confidence breakdown")
    
    # Quality metrics
    frame_quality_avg: Optional[float] = Field(None, description="Average frame quality for videos")
    variance: Optional[Dict[str, float]] = Field(None, description="Measurement variance")
    
    # Validation
    llm_validated: bool = Field(default=False)
    validation_result: Optional[Dict] = Field(None)
    
    # Manual input (if used)
    manual_input_used: bool = Field(default=False)
    manual_measurements: Optional[Dict[str, float]] = Field(None)
    
    # Anonymization
    user_id_hash: Optional[str] = Field(None, description="Anonymized user identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T10:00:00",
                "estimation_mode": "video",
                "detected_objects": [
                    {"class": "door", "confidence": 0.95},
                    {"class": "window", "confidence": 0.88}
                ],
                "reference_objects_used": ["door", "window"],
                "final_dimensions": {
                    "length": 12.5,
                    "width": 10.3,
                    "height": 10.0
                },
                "confidence_scores": {
                    "overall": 0.86,
                    "dimension": 0.88,
                    "detection": 0.84
                }
            }
        }


class DistributionUpdate(BaseModel):
    """Update to object size distribution."""
    
    object_type: str = Field(description="Type of object (door/window/etc)")
    old_mean: float = Field(description="Previous mean size")
    new_mean: float = Field(description="Updated mean size")
    old_std: float = Field(description="Previous standard deviation")
    new_std: float = Field(description="Updated standard deviation")
    update_timestamp: datetime = Field(default_factory=datetime.now)
    data_points_used: int = Field(description="Number of data points in update")
    
    class Config:
        json_schema_extra = {
            "example": {
                "object_type": "door",
                "old_mean": 7.0,
                "new_mean": 6.9,
                "old_std": 0.5,
                "new_std": 0.45,
                "data_points_used": 1000
            }
        }
