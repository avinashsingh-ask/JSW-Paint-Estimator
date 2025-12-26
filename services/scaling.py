"""Scaling service to convert pixel measurements to real-world dimensions."""
import numpy as np
from typing import Tuple, Optional, Dict, Any
from utils.image_utils import calculate_reference_scale


class ScalingService:
    """Service for pixel-to-real-world scaling."""
    
    def __init__(self):
        """Initialize scaling service."""
        self.scale_factor = None  # feet per pixel
        self.reference_object = None
    
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
        self.scale_factor = calculate_reference_scale(
            reference_object_pixels,
            reference_object_feet
        )
        self.reference_object = {
            "type": object_type,
            "size_pixels": reference_object_pixels,
            "size_feet": reference_object_feet,
            "scale_factor": self.scale_factor
        }
        return self.scale_factor
    
    def calibrate_from_detection(
        self,
        bbox: Dict[str, int],
        object_type: str = "door",
        standard_height: float = 7.0,
        standard_width: float = 3.0
    ) -> float:
        """
        Calibrate scale from a detected object with known dimensions.
        
        Args:
            bbox: Bounding box dictionary with keys {x, y, w, h}
            object_type: Type of object (door/window)
            standard_height: Standard height in feet
            standard_width: Standard width in feet
        
        Returns:
            Scale factor (feet per pixel)
        """
        # Use height for calibration (more reliable)
        height_pixels = bbox['h']
        
        # Use standard dimensions based on object type
        if object_type == "door":
            real_height = standard_height
        elif object_type == "window":
            real_height = 4.0  # Standard window height
        else:
            real_height = standard_height
        
        return self.calibrate_from_reference(
            reference_object_pixels=height_pixels,
            reference_object_feet=real_height,
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
        Estimate room dimensions from image.
        
        Args:
            image_shape: Image shape (height, width)
            detections: List of detected objects (optional)
        
        Returns:
            Dictionary with estimated dimensions {length, width, height}
        """
        if self.scale_factor is None and detections:
            # Try to calibrate from first door detection
            for detection in detections:
                if detection['class_name'] == 'door':
                    self.calibrate_from_detection(detection['bbox'], "door")
                    break
        
        if self.scale_factor is None:
            # Default assumption: standard room
            return {
                "length": 12.0,
                "width": 10.0,
                "height": 10.0,
                "estimated": True,
                "method": "default_assumption"
            }
        
        # Estimate from image dimensions
        height_pixels, width_pixels = image_shape
        
        estimated_width = self.pixels_to_feet(width_pixels)
        estimated_height = self.pixels_to_feet(height_pixels)
        
        # Assume room depth is similar to width (rough estimation)
        estimated_length = estimated_width
        
        # Room height estimation (typically 10 feet for residential)
        # If we have a door, we can estimate ceiling height
        ceiling_height = 10.0
        if detections:
            door_detections = [d for d in detections if d['class_name'] == 'door']
            if door_detections:
                # Assume door is 7 feet high, ceiling is 3 feet above
                ceiling_height = self.pixels_to_feet(door_detections[0]['bbox']['h']) + 3.0
        
        return {
            "length": round(estimated_length, 2),
            "width": round(estimated_width, 2),
            "height": round(ceiling_height, 2),
            "estimated": True,
            "method": "cv_estimation"
        }
    
    def get_calibration_info(self) -> Optional[Dict[str, Any]]:
        """Get current calibration information."""
        return self.reference_object
    
    def reset_calibration(self) -> None:
        """Reset calibration."""
        self.scale_factor = None
        self.reference_object = None
