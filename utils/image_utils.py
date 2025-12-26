"""Image processing utilities for OpenCV operations."""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List, Optional
import io


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Load image from bytes.
    
    Args:
        image_bytes: Image data in bytes
    
    Returns:
        Image as numpy array (BGR format)
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    # Decode image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Failed to decode image")
    
    return img


def validate_image(image: np.ndarray) -> bool:
    """
    Validate if image is valid.
    
    Args:
        image: Image as numpy array
    
    Returns:
        True if valid, False otherwise
    """
    if image is None:
        return False
    if len(image.shape) < 2:
        return False
    if image.size == 0:
        return False
    return True


def resize_image(
    image: np.ndarray,
    max_width: int = 1024,
    max_height: int = 1024
) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input image
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    # Calculate scaling factor
    scale = min(max_width / width, max_height / height, 1.0)
    
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for detection.
    
    Args:
        image: Input image
    
    Returns:
        Preprocessed image
    """
    # Resize if too large
    image = resize_image(image)
    
    # Denoise
    image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    
    # Enhance contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    image = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    return image


def detect_edges(image: np.ndarray) -> np.ndarray:
    """
    Detect edges in image using Canny edge detection.
    
    Args:
        image: Input image
    
    Returns:
        Edge map
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Canny edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    return edges


def find_contours(edge_image: np.ndarray) -> List[np.ndarray]:
    """
    Find contours in edge image.
    
    Args:
        edge_image: Binary edge image
    
    Returns:
        List of contours
    """
    contours, _ = cv2.findContours(
        edge_image,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    return contours


def draw_bounding_boxes(
    image: np.ndarray,
    boxes: List[Tuple[int, int, int, int]],
    labels: Optional[List[str]] = None,
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2
) -> np.ndarray:
    """
    Draw bounding boxes on image.
    
    Args:
        image: Input image
        boxes: List of bounding boxes (x, y, w, h)
        labels: Optional labels for each box
        color: Box color in BGR
        thickness: Line thickness
    
    Returns:
        Image with bounding boxes
    """
    result = image.copy()
    
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        
        if labels and i < len(labels):
            cv2.putText(
                result,
                labels[i],
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                thickness
            )
    
    return result


def image_to_bytes(image: np.ndarray, format: str = 'JPEG') -> bytes:
    """
    Convert image to bytes.
    
    Args:
        image: Image as numpy array
        format: Output format (JPEG, PNG, etc.)
    
    Returns:
        Image as bytes
    """
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert to PIL Image
    pil_image = Image.fromarray(image_rgb)
    
    # Save to bytes
    byte_io = io.BytesIO()
    pil_image.save(byte_io, format=format)
    byte_io.seek(0)
    
    return byte_io.getvalue()


def calculate_reference_scale(
    reference_object_pixels: float,
    reference_object_real_size: float
) -> float:
    """
    Calculate pixel-to-real-world scale factor.
    
    Args:
        reference_object_pixels: Size in pixels
        reference_object_real_size: Size in real world (feet)
    
    Returns:
        Scale factor (feet per pixel)
    """
    if reference_object_pixels <= 0:
        raise ValueError("Reference object size in pixels must be positive")
    
    return reference_object_real_size / reference_object_pixels
