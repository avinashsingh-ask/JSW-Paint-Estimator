"""CV-based estimation API endpoint (Scenario 2)."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from typing import Optional, Dict, Any, List
import json
from services.cv_pipeline import CVPipeline
from services.calculation_engine import CalculationEngine
from services.floorplan_analyzer import FloorPlanAnalyzer
from schemas.output_models import CVEstimationOutput, MultiRoomEstimationOutput, RoomEstimationOutput
from schemas.cv_models import CVRoomInput
from schemas.floorplan_models import FloorPlanResult
from utils.response_utils import success_response
from utils.image_utils import load_image_from_bytes

router = APIRouter(prefix="/api/v1/estimate", tags=["cv-estimation"])

# Initialize services
cv_pipeline = CVPipeline()
calc_engine = CalculationEngine()
floorplan_analyzer = FloorPlanAnalyzer()


@router.post("/cv/single-room", response_model=Dict[str, Any])
async def estimate_room_from_image(
    image: UploadFile = File(..., description="Room image"),
    room_type: str = Form(..., description="Room type (bedroom/hall/kitchen)"),
    paint_type: str = Form(default="interior", description="Paint type"),
    num_coats: int = Form(default=2, description="Number of coats"),
    include_ceiling: bool = Form(default=False, description="Paint ceiling"),
    length: Optional[float] = Form(default=None, description="Manual length override (feet)"),
    width: Optional[float] = Form(default=None, description="Manual width override (feet)"),
    height: Optional[float] = Form(default=None, description="Manual height override (feet)")
):
    """
    Estimate paint requirements from room image (Scenario 2).
    
    Uses OpenCV and YOLO to:
    - Detect doors and windows
    - Estimate room dimensions
    - Calculate paint requirements
    
    User can provide manual dimension overrides if needed.
    """
    try:
        # Read image
        image_bytes = await image.read()
        
        # Prepare manual dimensions
        manual_dims = {}
        if length:
            manual_dims['length'] = length
        if width:
            manual_dims['width'] = width
        if height:
            manual_dims['height'] = height
        
        # Process image with CV pipeline
        cv_result = cv_pipeline.process_image(
            image_bytes=image_bytes,
            reference_object_type="door",
            manual_dimensions=manual_dims if manual_dims else None
        )
        
        # Extract dimensions and counts
        dimensions = cv_result['dimensions']
        counts = cv_result['counts']
        
        # Calculate paint estimation
        estimation = calc_engine.calculate_room_estimation(
            length=dimensions['length'],
            width=dimensions['width'],
            height=dimensions['height'],
            num_doors=counts['doors'],
            num_windows=counts['windows'],
            paint_type=paint_type,
            num_coats=num_coats,
            include_ceiling=include_ceiling
        )
        
        # Create CV estimation output
        cv_estimation = CVEstimationOutput(
            **estimation.model_dump(),
            detection_results={
                "detected_doors": counts['doors'],
                "detected_windows": counts['windows'],
                "detections": cv_result['detections'],
                "total_detections": len(cv_result['detections'])
            },
            image_analysis={
                "dimensions_method": dimensions.get('method', 'cv_estimation'),
                "dimensions_estimated": dimensions.get('estimated', True),
                "image_shape": cv_result['image_shape'],
                "calibration": cv_result.get('calibration')
            }
        )
        
        return success_response(
            data=cv_estimation.model_dump(),
            message="CV-based estimation completed successfully"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV estimation failed: {str(e)}"
        )


@router.post("/cv/multi-room", response_model=Dict[str, Any])
async def estimate_multiple_rooms_from_images(
    images: List[UploadFile] = File(..., description="Room images"),
    room_data: str = Form(..., description="JSON string with room info")
):
    """
    Estimate paint requirements for multiple rooms from images.
    
    User provides:
    - Images of each room
    - Room types
    - Optional dimensions
    
    System returns:
    - Detection results for each room
    - Individual estimations
    - Total paint quantity
    - Total cost
    """
    print(f"\n✅ Multi-room endpoint reached!")
    print(f"   Images received: {len(images) if images else 'None'}")
    print(f"   Room data received: {bool(room_data)}")
    try:
        # Debug logging
        print(f"\n🔍 Multi-room request received:")
        print(f"   Number of images: {len(images)}")
        print(f"   Room data (raw): {room_data[:200]}...")  # First 200 chars
        
        # Parse room data
        rooms_info = json.loads(room_data)
        print(f"   Parsed rooms: {len(rooms_info)}")
        print(f"   Room info: {rooms_info}")
        
        if len(images) != len(rooms_info):
            error_msg = f"Number of images ({len(images)}) must match number of room configurations ({len(rooms_info)})"
            print(f"   ❌ Validation Error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Prepare room images for processing
        room_images = []
        for image, room_info in zip(images, rooms_info):
            image_bytes = await image.read()
            room_images.append((image_bytes, room_info))
        
        # Process all rooms
        cv_results = cv_pipeline.process_multiple_rooms(room_images)
        
        # Calculate estimations for each room
        room_estimations = []
        total_cost = 0.0
        total_paint = 0.0
        total_paintable_area = 0.0
        
        for cv_result, room_info in zip(cv_results, rooms_info):
            dimensions = cv_result['dimensions']
            counts = cv_result['counts']
            
            estimation = calc_engine.calculate_room_estimation(
                length=dimensions['length'],
                width=dimensions['width'],
                height=dimensions['height'],
                num_doors=counts['doors'],
                num_windows=counts['windows'],
                paint_type=room_info.get('paint_type', 'interior'),
                num_coats=room_info.get('num_coats', 2),
                include_ceiling=room_info.get('include_ceiling', False)
            )
            
            # Create CV estimation output
            cv_estimation = CVEstimationOutput(
                **estimation.model_dump(),
                detection_results={
                    "detected_doors": counts['doors'],
                    "detected_windows": counts['windows'],
                    "detections": cv_result['detections']
                },
                image_analysis={
                    "dimensions_method": dimensions.get('method'),
                    "dimensions_estimated": dimensions.get('estimated')
                }
            )
            
            room_estimations.append(
                RoomEstimationOutput(
                    room_name=room_info.get('room_name', f"Room {len(room_estimations) + 1}"),
                    room_type=cv_result['room_type'],
                    estimation=cv_estimation
                )
            )
            
            # Aggregate totals
            total_cost += estimation.cost_breakdown.total_cost
            total_paint += estimation.product_breakdown.paint.quantity
            total_paintable_area += estimation.area_calculation.paintable_area
        
        # Create multi-room output
        multi_room_output = MultiRoomEstimationOutput(
            rooms=room_estimations,
            total_summary={
                "total_rooms": len(room_estimations),
                "detection_method": "opencv_yolo",
                "all_rooms_processed": True
            },
            total_cost=round(total_cost, 2),
            total_paint_required=round(total_paint, 2),
            total_paintable_area=round(total_paintable_area, 2)
        )
        
        return success_response(
            data=multi_room_output.model_dump(),
            message=f"CV-based estimation completed for {len(room_estimations)} rooms"
        )
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room_data JSON format"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-room CV estimation failed: {str(e)}"
        )


@router.get("/cv/model-status", response_model=Dict[str, Any])
async def get_model_status():
    """Check if YOLO model is loaded and available."""
    model_loaded = cv_pipeline.is_model_loaded()
    
    return success_response(
        data={
            "yolo_model_loaded": model_loaded,
            "fallback_detection": not model_loaded,
            "status": "ready" if model_loaded else "using_fallback"
        },
        message="Model status retrieved"
    )


@router.post("/cv/video", response_model=Dict[str, Any])
async def estimate_room_from_video(
    video: UploadFile = File(..., description="Room walkthrough video"),
    room_type: str = Form(..., description="Room type (bedroom/hall/kitchen)"),
    paint_type: str = Form(default="interior", description="Paint type"),
    num_coats: int = Form(default=2, description="Number of coats"),
    include_ceiling: bool = Form(default=False, description="Paint ceiling"),
    length: Optional[float] = Form(default=None, description="Manual length override (feet)"),
    width: Optional[float] = Form(default=None, description="Manual width override (feet)"),
    height: Optional[float] = Form(default=None, description="Manual height override (feet)")
):
    """
    Estimate paint requirements from room video (Enhanced Scenario 2).
    
    User uploads a short room walkthrough video. The system:
    - Extracts frames at regular intervals
    - Detects doors and windows in each frame
    - Aggregates results for more accurate estimates
    - Calculates paint requirements
    
    This provides more comprehensive analysis than single images.
    """
    try:
        # Validate video format
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload a video file."
            )
        
        # Read video bytes
        video_bytes = await video.read()
        
        # Prepare manual dimensions
        manual_dims = {}
        if length:
            manual_dims['length'] = length
        if width:
            manual_dims['width'] = width
        if height:
            manual_dims['height'] = height
        
        # Process video with CV pipeline
        cv_result = cv_pipeline.process_video(
            video_bytes=video_bytes,
            filename=video.filename or "video.mp4",
            reference_object_type="door",
            manual_dimensions=manual_dims if manual_dims else None
        )
        
        # Extract aggregated dimensions and counts
        dimensions = cv_result['aggregated_dimensions']
        counts = cv_result['aggregated_counts']
        
        # Calculate paint estimation
        estimation = calc_engine.calculate_room_estimation(
            length=dimensions['length'],
            width=dimensions['width'],
            height=dimensions['height'],
            num_doors=counts['doors'],
            num_windows=counts['windows'],
            paint_type=paint_type,
            num_coats=num_coats,
            include_ceiling=include_ceiling
        )
        
        # Create comprehensive output
        video_estimation = {
            **estimation.model_dump(),
            "video_analysis": {
                "metadata": cv_result['metadata'],
                "frames_analyzed": cv_result['frame_count'],
                "detection_confidence": cv_result['detection_confidence'],
                "detections_summary": cv_result['detections_summary']
            },
            "detection_results": {
                "detected_doors": counts['doors'],
                "detected_windows": counts['windows'],
                "total_detections": cv_result['detections_summary']['total_detections']
            },
            "dimension_analysis": {
                "dimensions": dimensions,
                "method": dimensions.get('method', 'video_multi_frame_average'),
                "estimated": dimensions.get('estimated', True),
                "variance": dimensions.get('variance', {})
            }
        }
        
        return success_response(
            data=video_estimation,
            message=f"Video-based estimation completed successfully ({cv_result['frame_count']} frames analyzed)"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video estimation failed: {str(e)}"
        )


@router.post("/floorplan", response_model=Dict[str, Any])
async def estimate_from_floorplan(
    image: UploadFile = File(..., description="Architectural floor plan image"),
    ceiling_height: float = Form(default=10.0, description="Ceiling height in feet"),
    paint_type: str = Form(default="interior", description="Paint type (interior/exterior)"),
    num_coats: int = Form(default=2, description="Number of coats"),
    include_ceiling: bool = Form(default=False, description="Include ceiling painting")
):
    """
    Estimate paint requirements from architectural floor plan.
    
    The system will:
    - Extract text using OCR to find room dimensions
    - Detect room labels (Living Room, Bedroom, etc.)
    - Parse dimension annotations (e.g., "13'2\" x 9'1\"")
    - Calculate paint requirements for each room
    - Provide aggregated totals
    
    Example floor plan dimension formats supported:
    - 13'2" x 9'1" (feet and inches)
    - 27.11 x 31.4 (decimal feet)
    - 13-2 x 9-1 (feet-inches with hyphen)
    """
    try:
        # Validate inputs
        if ceiling_height < 7 or ceiling_height > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ceiling height must be between 7 and 20 feet"
            )
        
        if num_coats < 1 or num_coats > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of coats must be between 1 and 5"
            )
        
        # Read image
        image_bytes = await image.read()
        
        # Load image using utility function
        image_array = load_image_from_bytes(image_bytes)
        
        # Debug: Log image info
        print(f"🖼️  Floor plan image: {image_array.shape[1]}x{image_array.shape[0]} pixels")
        
        # Process floor plan
        result = floorplan_analyzer.process_floorplan(
            image=image_array,
            ceiling_height=ceiling_height,
            paint_type=paint_type,
            num_coats=num_coats,
            include_ceiling=include_ceiling
        )
        
        # Debug: Log OCR results
        print(f"📊 OCR Results:")
        print(f"   - Text regions: {result['ocr_metadata']['text_regions']}")
        print(f"   - Dimensions found: {result['ocr_metadata']['dimensions_found']}")
        print(f"   - Room labels found: {result['ocr_metadata']['room_labels_found']}")
        print(f"   - Total rooms extracted: {result['total_rooms']}")
        
        # Check if any rooms were extracted
        if result['total_rooms'] == 0:
            # Enhanced error message with debug info
            debug_message = f"No rooms with dimensions could be extracted. OCR found {result['ocr_metadata']['text_regions']} text regions but {result['ocr_metadata']['dimensions_found']} dimensions. Please ensure the image contains clear dimension annotations (e.g., 13'2\" x 9'1\")."
            
            return success_response(
                data=result,
                message=debug_message
            )
        
        return success_response(
            data=result,
            message=f"Floor plan analysis completed successfully. Extracted {result['total_rooms']} room(s)."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Floor plan analysis failed: {str(e)}"
        )
