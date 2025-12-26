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
        
        # Create visualization
        bbox_list = [d['bbox'] for d in detections]
        labels = [f"{d['class_name']} ({d['confidence']:.2f})" for d in detections]
        
        visualization = draw_bounding_boxes(
            image=image,
            boxes=[(b['x'], b['y'], b['w'], b['h']) for b in bbox_list],
            labels=labels
        )
        
        return {
            "dimensions": dimensions,
            "detections": detections,
            "counts": counts,
            "image_shape": {
                "height": image.shape[0],
                "width": image.shape[1]
            },
            "calibration": self.scaling_service.get_calibration_info(),
            "visualization": visualization
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
        
        # Initialize video processor
        video_processor = VideoProcessor()
        
        # Process video and extract frames
        video_data = video_processor.process_video(video_bytes, filename)
        frames = video_data['frames']
        metadata = video_data['metadata']
        
        # Process each frame
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
        
        # Aggregate results across all frames
        aggregated_results = self._aggregate_frame_results(
            frame_results,
            manual_dimensions
        )
        
        return {
            "metadata": metadata,
            "frame_count": len(frames),
            "frame_results": frame_results,
            "aggregated_dimensions": aggregated_results['dimensions'],
            "aggregated_counts": aggregated_results['counts'],
            "detection_confidence": aggregated_results['confidence'],
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
        
        # Aggregate dimensions (average across frames)
        lengths = [r['dimensions']['length'] for r in frame_results]
        widths = [r['dimensions']['width'] for r in frame_results]
        heights = [r['dimensions']['height'] for r in frame_results]
        
        avg_length = sum(lengths) / len(lengths)
        avg_width = sum(widths) / len(widths)
        avg_height = sum(heights) / len(heights)
        
        # Calculate variance for confidence estimation
        import statistics
        length_std = statistics.stdev(lengths) if len(lengths) > 1 else 0
        width_std = statistics.stdev(widths) if len(widths) > 1 else 0
        height_std = statistics.stdev(heights) if len(heights) > 1 else 0
        
        # Lower variance = higher confidence
        # Normalize to 0-1 scale (assuming std dev > 2 ft means low confidence)
        dimension_confidence = max(0.5, 1.0 - (length_std + width_std + height_std) / 6.0)
        
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
                "length": round(avg_length, 2),
                "width": round(avg_width, 2),
                "height": round(avg_height, 2),
                "estimated": True,
                "method": "video_multi_frame_average",
                "variance": {
                    "length_std": round(length_std, 2),
                    "width_std": round(width_std, 2),
                    "height_std": round(height_std, 2)
                }
            },
            "counts": {
                "doors": max_doors,
                "windows": max_windows
            },
            "confidence": {
                "dimension_confidence": round(dimension_confidence, 2),
                "detection_confidence": round(detection_confidence, 2),
                "overall_confidence": round((dimension_confidence + detection_confidence) / 2, 2)
            }
        }
    
    def is_model_loaded(self) -> bool:
        """Check if YOLO model is loaded."""
        return self.detection_service.is_model_loaded()

