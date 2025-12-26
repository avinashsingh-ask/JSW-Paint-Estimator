"""Schema module exports."""
from .manual_models import (
    RoomInput,
    ManualEstimationRequest,
    MultiRoomEstimationRequest
)
from .cv_models import (
    ReferenceObject,
    CVRoomInput,
    CVEstimationRequest,
    MultiRoomCVRequest,
    DetectionResult,
    RoomDetectionResult
)
from .output_models import (
    AreaCalculation,
    ProductQuantity,
    ProductBreakdown,
    CostBreakdown,
    EstimationOutput,
    RoomEstimationOutput,
    MultiRoomEstimationOutput,
    CVEstimationOutput,
    HealthCheckResponse,
    ErrorResponse
)

__all__ = [
    # Manual models
    'RoomInput',
    'ManualEstimationRequest',
    'MultiRoomEstimationRequest',
    # CV models
    'ReferenceObject',
    'CVRoomInput',
    'CVEstimationRequest',
    'MultiRoomCVRequest',
    'DetectionResult',
    'RoomDetectionResult',
    # Output models
    'AreaCalculation',
    'ProductQuantity',
    'ProductBreakdown',
    'CostBreakdown',
    'EstimationOutput',
    'RoomEstimationOutput',
    'MultiRoomEstimationOutput',
    'CVEstimationOutput',
    'HealthCheckResponse',
    'ErrorResponse',
]
