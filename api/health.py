"""Health check API endpoint."""
from fastapi import APIRouter
from schemas.output_models import HealthCheckResponse
from datetime import datetime
import os

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status, version, and model availability.
    """
    try:
        from services.detection import DetectionService
        detection_service = DetectionService()
        yolo_loaded = detection_service.is_model_loaded()
    except Exception:
        yolo_loaded = False
    
    return HealthCheckResponse(
        status="healthy",
        version=os.getenv("APP_VERSION", "1.0.0"),
        timestamp=datetime.now().isoformat(),
        models_loaded={
            "yolo": yolo_loaded
        }
    )
