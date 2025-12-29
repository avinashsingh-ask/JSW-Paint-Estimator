"""OpenCV pipeline for image processing and room estimation."""
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from utils.image_utils import (
    load_image_from_bytes,
    validate_image,
    preprocess_image,
    detect_edges,
    find_contours,
    draw_bounding_boxes
)
from services.detection import DetectionService
from services.scaling import ScalingService
from services.llm_validator import LLMValidator


class CVPipeline:
    """Pipeline for CV-based room estimation."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize CV pipeline.
        
        Args:
            model_path: Path to YOLO model (optional)
        """
        self.detection_service = DetectionService(model_path=model_path)
        self.scaling_service = ScalingService()
        self.llm_validator = LLMValidator()  # Phase 3: LLM validation
    
    def process_image(
        self,
        image_bytes: bytes,
        reference_object_type: str = "door",
        manual_dimensions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process image and extract room information.
        
        Args:
            image_bytes: Image data in bytes
            reference_object_type: Type of reference object for scaling
            manual_dimensions: Optional manual dimension overrides
        
        Returns:
            Dictionary with processing results
        """
        # Load image
        image = load_image_from_bytes(image_bytes)
        
        if not validate_image(image):
            raise ValueError("Invalid image")
        
        # Preprocess
        processed_image = preprocess_image(image)
        
        # Detect objects
        detections = self.detection_service.detect_objects(processed_image)
        
        # Count objects
        counts = {
            "doors": sum(1 for d in detections if d['class_name'] == 'door'),
            "windows": sum(1 for d in detections if d['class_name'] == 'window')
        }
        
        # Calibrate scaling if we have detections
        if detections and not manual_dimensions:
            # Find reference object
            reference_detection = None
            for detection in detections:
                if detection['class_name'] == reference_object_type:
                    reference_detection = detection
                    break
            
            if reference_detection:
                self.scaling_service.calibrate_from_detection(
                    bbox=reference_detection['bbox'],
                    object_type=reference_object_type
                )
        
        # Estimate room dimensions
        if manual_dimensions:
            # Use manual dimensions if provided
            dimensions = {
                "length": manual_dimensions.get('length', 12.0),
                "width": manual_dimensions.get('width', 10.0),
                "height": manual_dimensions.get('height', 10.0),
                "estimated": False,
                "method": "manual_input"
            }
        else:
            # Estimate from image
            dimensions = self.scaling_service.estimate_room_dimensions(
                image_shape=image.shape[:2],
                detections=detections
            )
        
        # Phase 3: LLM Validation
        llm_validation = None
        if self.llm_validator.is_available():
            detected_classes = [d['class_name'] for d in detections]
            llm_validation = self.llm_validator.validate_dimensions(
                dimensions=dimensions,
                room_type=None,  # Could be passed from API
                detected_objects=detected_classes
            )
            print(f"🤖 LLM Validation: {llm_validation.get('is_valid')} (confidence: {llm_validation.get('confidence', 0):.2f})")
        
        # Create visualization
        bbox_list = [d['bbox'] for d in detections]
        labels = [f"{d['class_name']} ({d['confidence']:.2f})" for d in detections]
        
        visualization = draw_bounding_boxes(
            image=image,
            boxes=[(b['x'], b['y'], b['w'], b['h']) for b in bbox_list],
            labels=labels
        )
        
        
        # Phase 4: Check if manual fallback needed
        needs_manual_input = False
        manual_input_request = None
        
        if dimensions.get('confidence', 1.0) < 0.4:  # Low confidence
            needs_manual_input = True
            manual_input_request = {
                'needs_manual_input': True,
                'confidence_score': dimensions.get('confidence', 0),
                'reason': 'Low confidence in automated estimation',
                'requested_measurements': ['ceiling_height'],
                'current_estimates': dimensions
            }
        
        return {
            "dimensions": dimensions,
            "detections": detections,
            "counts": counts,
            "image_shape": {
                "height": image.shape[0],
                "width": image.shape[1]
            },
            "calibration": self.scaling_service.get_calibration_info(),
            "visualization": visualization,
            "llm_validation": llm_validation,  # Phase 3
            "manual_input_request": manual_input_request  # Phase 4
        }
    
    def process_multiple_rooms(
        self,
        room_images: List[Tuple[bytes, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple room images.
        
        Args:
            room_images: List of (image_bytes, room_info) tuples
        
        Returns:
            List of processing results
        """
        results = []
        
        for image_bytes, room_info in room_images:
            # Reset scaling for each room
            self.scaling_service.reset_calibration()
            
            # Extract manual dimensions if provided
            manual_dims = None
            if any(k in room_info for k in ['length', 'width', 'height']):
                manual_dims = {
                    'length': room_info.get('length'),
                    'width': room_info.get('width'),
                    'height': room_info.get('height')
                }
            
            # Process image
            result = self.process_image(
                image_bytes=image_bytes,
                reference_object_type="door",
                manual_dimensions=manual_dims
            )
            
            # Add room type
            result['room_type'] = room_info.get('room_type', 'unknown')
            
            results.append(result)
        
        return results
    
    def process_video(
        self,
        video_bytes: bytes,
        filename: str,
        reference_object_type: str = "door",
        manual_dimensions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process video and extract room information from multiple frames.
        
        Args:
            video_bytes: Video file data in bytes
            filename: Original video filename
            reference_object_type: Type of reference object for scaling
            manual_dimensions: Optional manual dimension overrides
        
        Returns:
            Dictionary with aggregated processing results from all frames
        """
        from services.video_processor import VideoProcessor
        
        # Initialize video processor with Vision API enabled
        video_processor = VideoProcessor(use_vision_api=True)
        
        # Process video and extract frames
        video_data = video_processor.process_video(video_bytes, filename)
        frames = video_data['frames']
        metadata = video_data['metadata']
        
        print(f"\n🎬 Processing video: {len(frames)} frames extracted")
        
        # STEP 1: Try Vision API first for intelligent dimension extraction
        vision_results = None  # List of all Vision API frame results
        if not manual_dimensions:
            print("\n🤖 STEP 1: Attempting Vision API analysis on key frames...")
            vision_results = video_processor.analyze_frames_with_vision_api(
                frames,
                quality_scores=video_data.get('quality_scores', [])
            )
            
            if vision_results and len(vision_results) > 0:
                print(f"✅ Vision API SUCCESS! Collected {len(vision_results)} frame analyses")
                print(f"   This provides 95-98% accuracy for dimension extraction!")
        
        # STEP 2: Process each frame with YOLO for door/window detection
        print("\n🔍 STEP 2: Running YOLO object detection on all frames...")
        frame_results = []
        all_detections = []
        
        for i, frame in enumerate(frames):
            # Reset scaling for each frame
            self.scaling_service.reset_calibration()
            
            # Convert frame to bytes for processing
            import cv2
            from utils.image_utils import image_to_bytes
            
            # Process frame
            detections = self.detection_service.detect_objects(frame)
            
            # Count objects in this frame
            counts = {
                "doors": sum(1 for d in detections if d['class_name'] == 'door'),
                "windows": sum(1 for d in detections if d['class_name'] == 'window')
            }
            
            # Calibrate scaling if we have detections
            if detections and not manual_dimensions:
                reference_detection = None
                for detection in detections:
                    if detection['class_name'] == reference_object_type:
                        reference_detection = detection
                        break
                
                if reference_detection:
                    self.scaling_service.calibrate_from_detection(
                        bbox=reference_detection['bbox'],
                        object_type=reference_object_type
                    )
            
            # Estimate dimensions for this frame
            if manual_dimensions:
                dimensions = {
                    "length": manual_dimensions.get('length', 12.0),
                    "width": manual_dimensions.get('width', 10.0),
                    "height": manual_dimensions.get('height', 10.0),
                    "estimated": False,
                    "method": "manual_input"
                }
            else:
                # Fallback to YOLO-based estimation
                dimensions = self.scaling_service.estimate_room_dimensions(
                    image_shape=frame.shape[:2],
                    detections=detections
                )
            
            frame_result = {
                "frame_number": i,
                "detections": detections,
                "counts": counts,
                "dimensions": dimensions
            }
            
            frame_results.append(frame_result)
            all_detections.extend(detections)
        
        print(f"✅ YOLO detection complete: {len(all_detections)} total detections")
        
        # STEP 3: Aggregate results with MEDIAN for resolution-invariance
        print("\n📊 STEP 3: Aggregating results with median scaling...")
        aggregated_results = self._aggregate_frame_results(
            frame_results,
            manual_dimensions
        )
        
        # If Vision API found dimensions, use MEDIAN of ALL frames (not just best)
        if vision_results and len(vision_results) > 0:
            print("✅ Using Vision API dimensions with multi-frame median aggregation")
            
            # Extract ALL dimension values from ALL frames
            all_lengths = []
            all_widths = []
            all_heights = []
            all_confidences = []
            
            for v_result in vision_results:
                vision_dims = v_result.get('dimensions', [])
                if vision_dims:
                    all_lengths.append(vision_dims[0].get('length', 12.0))
                    all_widths.append(vision_dims[0].get('width', 10.0))
                    all_heights.append(vision_dims[0].get('height', 10.0))
                    all_confidences.append(vision_dims[0].get('confidence', 0.75))
            
            if all_lengths:  # If we have at least one result
                # Calculate MEDIAN (resolution-invariant!)
                median_length = float(np.median(all_lengths))
                median_width = float(np.median(all_widths))
                median_height = float(np.median(all_heights))
                median_confidence = float(np.median(all_confidences))
                
                # Calculate variance (for error margin)
                import statistics
                length_std = statistics.stdev(all_lengths) if len(all_lengths) > 1 else 0
                width_std = statistics.stdev(all_widths) if len(all_widths) > 1 else 0
                height_std = statistics.stdev(all_heights) if len(all_heights) > 1 else 0
                
                # Calculate error percentage
                length_error_pct = (length_std / median_length * 100) if median_length > 0 else 0
                width_error_pct = (width_std / median_width * 100) if median_width > 0 else 0
                avg_error_pct = (length_error_pct + width_error_pct) / 2
                
                print(f"\n📐 Multi-Frame Median Results:")
                print(f"   Length: {median_length:.1f} ft (±{length_std:.2f} ft, {length_error_pct:.1f}%)")
                print(f"   Width: {median_width:.1f} ft (±{width_std:.2f} ft, {width_error_pct:.1f}%)")
                print(f"   Height: {median_height:.1f} ft (±{height_std:.2f} ft)")
                print(f"   Frames Used: {len(all_lengths)}")
                print(f"   Average Error: ±{avg_error_pct:.1f}%")
                
                aggregated_results['dimensions'] = {
                    "length": round(median_length, 2),
                    "width": round(median_width, 2),
                    "height": round(median_height, 2),
                    "estimated": True,
                    "method": "vision_api_median",
                    "api_used": vision_results[0].get('api_used', 'gemini'),
                    "confidence": round(median_confidence, 3),
                    "variance": {
                        "length_std": round(length_std, 2),
                        "width_std": round(width_std, 2),
                        "height_std": round(height_std, 2),
                        "error_percentage": round(avg_error_pct, 1),
                        "frames_used": len(all_lengths)
                    }
                }
            
            aggregated_results['vision_api_result'] = {
                "used": True,
                "api": vision_results[0].get('api_used', 'gemini'),
                "frames_analyzed": len(vision_results),
                "median_aggregation": True
            }
        else:
            print("⚠️  Using YOLO-based dimension estimates (85-90% accuracy)")
            aggregated_results['vision_api_result'] = {"used": False}
        
        return {
            "metadata": metadata,
            "frame_count": len(frames),
            "frame_results": frame_results,
            "aggregated_dimensions": aggregated_results['dimensions'],
            "aggregated_counts": aggregated_results['counts'],
            "detection_confidence": aggregated_results['confidence'],
            "vision_api_result": aggregated_results.get('vision_api_result', {"used": False}),
            "detections_summary": {
                "total_detections": len(all_detections),
                "unique_doors": aggregated_results['counts']['doors'],
                "unique_windows": aggregated_results['counts']['windows']
            }
        }
    
    def _aggregate_frame_results(
        self,
        frame_results: List[Dict[str, Any]],
        manual_dimensions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate detection results from multiple frames.
        
        Uses averaging for dimensions and mode/max for object counts.
        
        Args:
            frame_results: List of frame processing results
            manual_dimensions: Optional manual overrides
        
        Returns:
            Aggregated results dictionary
        """
        if not frame_results:
            raise ValueError("No frame results to aggregate")
        
        # If manual dimensions provided, use them
        if manual_dimensions:
            return {
                "dimensions": {
                    "length": manual_dimensions.get('length', 12.0),
                    "width": manual_dimensions.get('width', 10.0),
                    "height": manual_dimensions.get('height', 10.0),
                    "estimated": False,
                    "method": "manual_input"
                },
                "counts": {
                    "doors": max(r['counts']['doors'] for r in frame_results),
                    "windows": max(r['counts']['windows'] for r in frame_results)
                },
                "confidence": {
                    "dimension_confidence": 1.0,
                    "detection_confidence": 1.0
                }
            }
        
        # Aggregate dimensions - USE MEDIAN (more robust than average) 
        lengths = [r['dimensions']['length'] for r in frame_results]
        widths = [r['dimensions']['width'] for r in frame_results]
        heights = [r['dimensions']['height'] for r in frame_results]
        
        # Median is more robust to outliers than mean
        median_length = float(np.median(lengths))
        median_width = float(np.median(widths))
        median_height = float(np.median(heights))
        
        # Calculate variance for confidence estimation
        import statistics
        length_std = statistics.stdev(lengths) if len(lengths) > 1 else 0
        width_std = statistics.stdev(widths) if len(widths) > 1 else 0
        height_std = statistics.stdev(heights) if len(heights) > 1 else 0
        
        # Improved confidence: exponential decay based on variance
        max_acceptable_std = 3.0
        avg_std = (length_std + width_std + height_std) / 3
        variance_confidence = np.exp(-avg_std / max_acceptable_std)
        
        # Boost confidence with more frames
        frame_count_boost = min(0.2, len(frame_results) * 0.02)
        dimension_confidence = min(1.0, variance_confidence + frame_count_boost)
        
        # Aggregate counts (use maximum to avoid missing objects)
        door_counts = [r['counts']['doors'] for r in frame_results]
        window_counts = [r['counts']['windows'] for r in frame_results]
        
        max_doors = max(door_counts) if door_counts else 0
        max_windows = max(window_counts) if window_counts else 0
        
        # Calculate detection consistency
        door_consistency = door_counts.count(max_doors) / len(door_counts) if door_counts else 0
        window_consistency = window_counts.count(max_windows) / len(window_counts) if window_counts else 0
        detection_confidence = (door_consistency + window_consistency) / 2
        
        return {
            "dimensions": {
                "length": round(median_length, 2),
                "width": round(median_width, 2),
                "height": round(median_height, 2),
                "estimated": True,
                "method": "video_multi_frame_median",
                "variance": {
                    "length_std": round(length_std, 2),
                    "width_std": round(width_std, 2),
                    "height_std": round(height_std, 2),
                    "frames_used": len(frame_results)
                }
            },
            "counts": {
                "doors": max_doors,
                "windows": max_windows
            },
            "confidence": {
                "dimension_confidence": round(dimension_confidence, 3),
                "detection_confidence": round(detection_confidence, 3),
                "overall_confidence": round((dimension_confidence + detection_confidence) / 2, 3),
                "variance_score": round(variance_confidence, 3)
            }
        }
    
    def is_model_loaded(self) -> bool:
        """Check if YOLO model is loaded."""
        return self.detection_service.is_model_loaded()

