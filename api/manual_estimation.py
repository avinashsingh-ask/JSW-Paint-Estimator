"""Manual estimation API endpoint (Scenario 1)."""
from fastapi import APIRouter, HTTPException, status
from schemas.manual_models import ManualEstimationRequest, MultiRoomEstimationRequest
from schemas.output_models import EstimationOutput, MultiRoomEstimationOutput, RoomEstimationOutput
from services.calculation_engine import CalculationEngine
from utils.response_utils import success_response, error_response
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/estimate", tags=["manual-estimation"])

# Initialize calculation engine
calc_engine = CalculationEngine()


@router.post("/manual", response_model=Dict[str, Any])
async def estimate_single_room(request: ManualEstimationRequest):
    """
    Estimate paint requirements for a single room (Scenario 1).
    
    User provides:
    - Room dimensions (length, width, height)
    - Number of doors and windows
    - Paint type (interior/exterior)
    - Number of coats
    
    System returns:
    - Paintable area (sq ft)
    - Paint required (liters)
    - Estimated cost (₹)
    - Product-wise breakdown (primer, putty, paint)
    """
    try:
        # Calculate estimation
        estimation = calc_engine.calculate_room_estimation(
            length=request.room.length,
            width=request.room.width,
            height=request.room.height,
            num_doors=request.room.num_doors,
            num_windows=request.room.num_windows,
            door_height=request.room.door_height,
            door_width=request.room.door_width,
            window_height=request.room.window_height,
            window_width=request.room.window_width,
            paint_type=request.paint_type,
            paint_product=request.paint_product,
            num_coats=request.num_coats,
            include_ceiling=request.include_ceiling
        )
        
        return success_response(
            data=estimation.model_dump(),
            message="Paint estimation completed successfully"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Estimation failed: {str(e)}"
        )


@router.post("/manual/multi-room", response_model=Dict[str, Any])
async def estimate_multiple_rooms(request: MultiRoomEstimationRequest):
    """
    Estimate paint requirements for multiple rooms.
    
    User provides:
    - List of rooms with dimensions
    - Paint type
    - Number of coats
    
    System returns:
    - Individual room estimations
    - Total paint quantity
    - Total cost
    - Aggregate product breakdown
    """
    try:
        room_estimations = []
        total_cost = 0.0
        total_paint = 0.0
        total_paintable_area = 0.0
        total_primer = 0.0
        total_putty = 0.0
        
        # Process each room
        for idx, room in enumerate(request.rooms):
            estimation = calc_engine.calculate_room_estimation(
                length=room.length,
                width=room.width,
                height=room.height,
                num_doors=room.num_doors,
                num_windows=room.num_windows,
                door_height=room.door_height,
                door_width=room.door_width,
                window_height=room.window_height,
                window_width=room.window_width,
                paint_type=request.paint_type,
                paint_product=request.paint_product,
                num_coats=request.num_coats,
                include_ceiling=request.include_ceilings
            )
            
            room_estimations.append(
                RoomEstimationOutput(
                    room_name=f"Room {idx + 1}",
                    estimation=estimation
                )
            )
            
            # Aggregate totals
            total_cost += estimation.cost_breakdown.total_cost
            total_paint += estimation.product_breakdown.paint.quantity
            total_paintable_area += estimation.area_calculation.paintable_area
            
            if estimation.product_breakdown.primer:
                total_primer += estimation.product_breakdown.primer.quantity
            if estimation.product_breakdown.putty:
                total_putty += estimation.product_breakdown.putty.quantity
        
        # Create multi-room output
        multi_room_output = MultiRoomEstimationOutput(
            rooms=room_estimations,
            total_summary={
                "total_rooms": len(request.rooms),
                "paint_type": request.paint_type,
                "num_coats": request.num_coats,
                "total_primer_liters": round(total_primer, 2),
                "total_putty_kg": round(total_putty, 2),
                "total_paint_liters": round(total_paint, 2)
            },
            total_cost=round(total_cost, 2),
            total_paint_required=round(total_paint, 2),
            total_paintable_area=round(total_paintable_area, 2)
        )
        
        return success_response(
            data=multi_room_output.model_dump(),
            message=f"Estimation completed for {len(request.rooms)} rooms"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-room estimation failed: {str(e)}"
        )
