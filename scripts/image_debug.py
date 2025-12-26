"""
Image debugging script for testing CV pipeline.
"""
import cv2
import numpy as np
from services.cv_pipeline import CVPipeline
from services.detection import DetectionService
import sys


def test_image_processing(image_path: str):
    """Test image processing pipeline."""
    print(f"🔍 Testing image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return
    
    print(f"✓ Image loaded: {image.shape}")
    
    # Initialize services
    pipeline = CVPipeline()
    detection_service = DetectionService()
    
    # Check model status
    if detection_service.is_model_loaded():
        print("✓ YOLO model loaded")
    else:
        print("⚠ Using fallback detection (YOLO not available)")
    
    # Detect objects
    print("\n🔎 Detecting objects...")
    detections = detection_service.detect_objects(image)
    
    print(f"Found {len(detections)} objects:")
    for detection in detections:
        print(f"  - {detection['class_name']}: {detection['confidence']:.2f}")
    
    # Count objects
    counts = detection_service.count_objects(image)
    print(f"\n📊 Object counts:")
    print(f"  Doors: {counts['door']}")
    print(f"  Windows: {counts['window']}")
    print(f"  Total: {counts['total']}")
    
    # Draw detections
    from utils.image_utils import draw_bounding_boxes
    
    bbox_list = [d['bbox'] for d in detections]
    labels = [f"{d['class_name']} ({d['confidence']:.2f})" for d in detections]
    
    visualization = draw_bounding_boxes(
        image=image.copy(),
        boxes=[(b['x'], b['y'], b['w'], b['h']) for b in bbox_list],
        labels=labels
    )
    
    # Save visualization
    output_path = image_path.replace('.', '_detected.')
    cv2.imwrite(output_path, visualization)
    print(f"\n💾 Visualization saved to: {output_path}")
    
    # Display (if running in GUI environment)
    try:
        cv2.imshow('Detections', visualization)
        print("\n👁️  Press any key to close the window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("⚠ Cannot display image (no GUI environment)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/image_debug.py <image_path>")
        print("Example: python scripts/image_debug.py test_room.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_image_processing(image_path)
