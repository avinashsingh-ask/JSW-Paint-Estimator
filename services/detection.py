"""Object detection service using YOLO."""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import os


class DetectionService:
    """Service for detecting doors and windows using YOLO."""
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize detection service.
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path or os.getenv("YOLO_MODEL_PATH", "cv_models/yolo/best.pt")
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.model_loaded = False
        
        # Try to load model
        self._load_model()
    
    def _load_model(self) -> None:
        """Load YOLO model."""
        try:
            from ultralytics import YOLO
            
            model_path = Path(self.model_path)
            if model_path.exists():
                self.model = YOLO(str(model_path))
                self.model_loaded = True
                print(f"✓ YOLO model loaded from {self.model_path}")
            else:
                print(f"⚠ YOLO model not found at {self.model_path}")
                print("  Using fallback detection methods.")
                self.model_loaded = False
        except ImportError:
            print("⚠ Ultralytics YOLO not available. Using fallback detection.")
            self.model_loaded = False
        except Exception as e:
            print(f"⚠ Error loading YOLO model: {e}")
            self.model_loaded = False
    
    def detect_objects(
        self,
        image: np.ndarray,
        target_classes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect objects in image.
        
        Args:
            image: Input image
            target_classes: List of class names to detect (e.g., ['door', 'window'])
        
        Returns:
            List of detection dictionaries with keys:
                - class_name: Detected object class
                - confidence: Detection confidence
                - bbox: Bounding box (x, y, w, h)
        """
        if target_classes is None:
            target_classes = ['door', 'window']
        
        # IMPORTANT: YOLO model is pretrained COCO (80 classes) without door/window classes
        # Always use fallback CV detection for door/window detection
        # For other object types, could use YOLO if needed in future
        return self._detect_with_fallback(image, target_classes)
    
    def _detect_with_yolo(
        self,
        image: np.ndarray,
        target_classes: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect using YOLO model."""
        detections = []
        
        try:
            # Run inference
            results = self.model(image, conf=self.confidence_threshold)
            
            # Parse results
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get class name
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id].lower()
                    
                    # Filter by target classes
                    if class_name in target_classes:
                        # Get bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        w = x2 - x1
                        h = y2 - y1
                        
                        # Get confidence
                        confidence = float(box.conf[0])
                        
                        detections.append({
                            "class_name": class_name,
                            "confidence": confidence,
                            "bbox": {
                                "x": int(x1),
                                "y": int(y1),
                                "w": int(w),
                                "h": int(h)
                            }
                        })
        except Exception as e:
            print(f"Error during YOLO detection: {e}")
            return self._detect_with_fallback(image, target_classes)
        
        return detections
    
    def _detect_with_fallback(
        self,
        image: np.ndarray,
        target_classes: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fallback detection using traditional CV methods.
        Uses edge detection and contour analysis to find rectangular shapes.
        Classifies them as doors/windows based on aspect ratio.
        """
        detections = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply edge detection with adaptive thresholds
        edges = cv2.Canny(blurred, 30, 100)
        
        # Dilate edges to connect broken lines
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and aspect ratio
        height, width = image.shape[:2]
        min_area = (width * height) * 0.005  # Minimum 0.5% of image area (reduced from 1%)
        max_area = (width * height) * 0.5    # Maximum 50% of image area
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if min_area < area < max_area:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Calculate how rectangular the contour is
                rect_area = w * h
                extent = area / rect_area if rect_area > 0 else 0
                
                # Only consider roughly rectangular shapes (>40% filled)
                if extent < 0.4:
                    continue
                
                # Classify based on aspect ratio:
                # Doors: taller than wide (aspect ratio 0.3-0.75)
                # Windows: wider or square (aspect ratio 0.75-3.0)
                if 0.3 < aspect_ratio < 0.75:
                    class_name = "door"
                    confidence = 0.65
                elif 0.75 <= aspect_ratio < 3.0:
                    class_name = "window"
                    confidence = 0.70
                else:
                    continue
                
                # Filter by target classes
                if class_name in target_classes:
                    detections.append({
                        "class_name": class_name,
                        "confidence": confidence,
                        "bbox": {
                            "x": x,
                            "y": y,
                            "w": w,
                            "h": h
                        }
                    })
        
        return detections
    
    def count_objects(
        self,
        image: np.ndarray,
        object_type: str = None
    ) -> Dict[str, int]:
        """
        Count detected objects.
        
        Args:
            image: Input image
            object_type: Specific object type to count (optional)
        
        Returns:
            Dictionary with object counts
        """
        detections = self.detect_objects(image)
        
        counts = {"door": 0, "window": 0, "total": 0}
        
        for detection in detections:
            class_name = detection["class_name"]
            if class_name in counts:
                counts[class_name] += 1
        
        counts["total"] = counts["door"] + counts["window"]
        
        if object_type:
            return {object_type: counts.get(object_type, 0)}
        
        return counts
    
    def is_model_loaded(self) -> bool:
        """Check if YOLO model is loaded."""
        return self.model_loaded
