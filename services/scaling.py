"""Scaling service to convert pixel measurements to real-world dimensions.

This service now uses probabilistic scale inference instead of fixed constants.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from services.scale_inference import ScaleInference
from services.confidence_scoring import ConfidenceScoring


class ScalingService:
    """Service for pixel-to-real-world scaling with probabilistic inference."""
    
    def __init__(self):
        """Initialize scaling service."""
        self.scale_factor = None  # feet per pixel
        self.reference_object = None
        self.scale_inference = ScaleInference()
        self.confidence_scoring = ConfidenceScoring()
        
        # Resolution normalization
        self.original_resolution = None
        self.inference_resolution = None
        self.scale_x = 1.0
        self.scale_y = 1.0
    
    def set_resolution_mapping(
        self,
        original_shape: Tuple[int, int],
        inference_shape: Tuple[int, int]
    ):
        """
        Set resolution mapping for coordinate transformation.
        
        Args:
            original_shape: Original image shape (height, width)
            inference_shape: Inference/resized image shape (height, width)
        """
        self.original_resolution = original_shape
        self.inference_resolution = inference_shape
        
        # Calculate scale factors
        self.scale_y = original_shape[0] / inference_shape[0]
        self.scale_x = original_shape[1] / inference_shape[1]
    
    def map_to_original_coordinates(
        self,
        bbox: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Map bounding box from inference resolution to original resolution.
        
        Args:
            bbox: Bounding box from inference image
        
        Returns:
            Bounding box in original resolution coordinates
        """
        return {
            'x': int(bbox['x'] * self.scale_x),
            'y': int(bbox['y'] * self.scale_y),
            'w': int(bbox['w'] * self.scale_x),
            'h': int(bbox['h'] * self.scale_y)
        }
    
    def calibrate_from_detections_probabilistic(
        self,
        detections: List[Dict],
        image_shape: Tuple[int, int]
    ) -> Dict:
        """
        Calibrate scale using probabilistic inference from multiple detections.
        
        Args:
            detections: List of detected objects
            image_shape: Image shape (height, width)
        
        Returns:
            Scale inference result with confidence
        """
        # Use probabilistic scale inference
        result = self.scale_inference.infer_scale(
            detections=detections,
            image_shape=image_shape,
            fusion_method='weighted_median'
        )
        
        if result['scale'] is not None:
            self.scale_factor = result['scale']
            self.reference_object = {
                "method": "probabilistic_inference",
                "candidates_count": result['candidates_count'],
                "confidence": result['confidence'],
                "scale_factor": result['scale']
            }
        
        return result
    
    def calibrate_from_reference(
        self,
        reference_object_pixels: float,
        reference_object_feet: float,
        object_type: str = "door"
    ) -> float:
        """
        Calibrate scale using a reference object.
        
        Args:
            reference_object_pixels: Size of reference object in pixels
            reference_object_feet: Known size of reference object in feet
            object_type: Type of reference object
        
        Returns:
            Scale factor (feet per pixel)
        """
        if reference_object_pixels <= 0:
            raise ValueError("Reference object pixels must be > 0")
        
        self.scale_factor = reference_object_feet / reference_object_pixels
        self.reference_object = {
            "type": object_type,
            "size_pixels": reference_object_pixels,
            "size_feet": reference_object_feet,
            "scale_factor": self.scale_factor,
            "method": "manual_reference"
        }
        return self.scale_factor
    
    def calibrate_from_detection(
        self,
        bbox: Dict[str, int],
        object_type: str = "door"
    ) -> float:
        """
        Calibrate scale from a single detected object (legacy method).
        
        Now uses probabilistic distribution instead of fixed size.
        
        Args:
            bbox: Bounding box dictionary with keys {x, y, w, h}
            object_type: Type of object (door/window)
        
        Returns:
            Scale factor (feet per pixel)
        """
        # Get distribution for this object type
        if object_type in self.scale_inference.distributions:
            dist = self.scale_inference.distributions[object_type]
            real_size = dist.mean  # Use distribution mean
        else:
            # Fallback for unknown object types
            real_size = 7.0  # Default door height
        
        # Use height for calibration
        height_pixels = bbox['h']
        
        return self.calibrate_from_reference(
            reference_object_pixels=height_pixels,
            reference_object_feet=real_size,
            object_type=object_type
        )
    
    def pixels_to_feet(self, pixels: float) -> float:
        """
        Convert pixels to feet.
        
        Args:
            pixels: Measurement in pixels
        
        Returns:
            Measurement in feet
        """
        if self.scale_factor is None:
            raise ValueError("Scale factor not set. Please calibrate first.")
        
        return round(pixels * self.scale_factor, 2)
    
    def feet_to_pixels(self, feet: float) -> float:
        """
        Convert feet to pixels.
        
        Args:
            feet: Measurement in feet
        
        Returns:
            Measurement in pixels
        """
        if self.scale_factor is None:
            raise ValueError("Scale factor not set. Please calibrate first.")
        
        return round(feet / self.scale_factor, 2)
    
    def estimate_room_dimensions(
        self,
        image_shape: Tuple[int, int],
        detections: list = None
    ) -> Dict[str, float]:
        """
        Estimate room dimensions from image using probabilistic inference.
        
        Args:
            image_shape: Image shape (height, width)
            detections: List of detected objects (optional)
        
        Returns:
            Dictionary with estimated dimensions {length, width, height}
        """
        # Try probabilistic calibration if we have detections
        if detections:
            scale_result = self.calibrate_from_detections_probabilistic(
                detections=detections,
                image_shape=image_shape
            )
        
        if self.scale_factor is None:
            # No valid scale could be determined
            return {
                "length": 12.0,
                "width": 10.0,
                "height": 10.0,
                "estimated": True,
                "method": "default_assumption",
                "confidence": 0.3
            }
        
        # Estimate from image dimensions
        height_pixels, width_pixels = image_shape
        
        estimated_width = self.pixels_to_feet(width_pixels)
        estimated_height = self.pixels_to_feet(height_pixels)
        
        # Assume room depth is similar to width (rough estimation)
        estimated_length = estimated_width
        
        # Room height estimation
        ceiling_height = 10.0
        if detections:
            door_detections = [d for d in detections if d['class_name'] == 'door']
            if door_detections:
                # Use door detection to estimate ceiling
                door_dist = self.scale_inference.distributions.get('door')
                if door_dist:
                    door_height = door_dist.mean
                    ceiling_height = door_height + 3.0  # Add 3ft above door
        
        # Calculate confidence
        scale_confidence = self.reference_object.get('confidence', 0.7) if self.reference_object else 0.5
        dimension_confidence = self.confidence_scoring.calculate_dimension_confidence(
            scale_confidence=scale_confidence,
            estimation_method='cv_estimation'
        )
        
        return {
            "length": round(estimated_length, 2),
            "width": round(estimated_width, 2),
            "height": round(ceiling_height, 2),
            "estimated": True,
            "method": "cv_estimation",
            "confidence": round(dimension_confidence, 3)
        }
    
    def get_calibration_info(self) -> Optional[Dict[str, Any]]:
        """Get current calibration information."""
        return self.reference_object
    
    def reset_calibration(self) -> None:
        """Reset calibration."""
        self.scale_factor = None
        self.reference_object = None
        self.original_resolution = None
        self.inference_resolution = None
        self.scale_x = 1.0
        self.scale_y = 1.0
