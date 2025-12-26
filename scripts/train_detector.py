"""
Script placeholder for training YOLO detector for door/window detection.

To train a custom YOLO model:
1. Collect and label images with doors and windows
2. Use a tool like Roboflow or LabelImg for annotation
3. Export in YOLO format
4. Use this script to train the model

For now, this is a placeholder that shows the structure.
"""

from ultralytics import YOLO
import os


def train_detector(
    data_yaml: str = "data/doors_windows.yaml",
    epochs: int = 100,
    img_size: int = 640,
    batch_size: int = 16
):
    """
    Train YOLO model for door and window detection.
    
    Args:
        data_yaml: Path to data configuration YAML
        epochs: Number of training epochs
        img_size: Image size for training
        batch_size: Batch size
    """
    print("🚀 Starting YOLO training...")
    
    # Load a pretrained model (recommended for transfer learning)
    model = YOLO('yolov8n.pt')  # nano model for faster training
    
    # Train the model
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        name='door_window_detector',
        project='cv_models/yolo',
        patience=50,
        save=True,
        device=0  # Use GPU if available, otherwise CPU
    )
    
    print("✓ Training complete!")
    print(f"📊 Results saved to: cv_models/yolo/door_window_detector")
    
    # Validate the model
    metrics = model.val()
    print(f"\n📈 Validation Metrics:")
    print(f"  mAP50: {metrics.box.map50:.3f}")
    print(f"  mAP50-95: {metrics.box.map:.3f}")
    
    # Export the best model
    best_model_path = "cv_models/yolo/door_window_detector/weights/best.pt"
    if os.path.exists(best_model_path):
        print(f"\n💾 Best model: {best_model_path}")
        print("   Copy this to: cv_models/yolo/best.pt")


def create_sample_data_yaml():
    """Create sample data.yaml configuration."""
    yaml_content = """
# Door and Window Detection Dataset

# Paths
path: ../datasets/door_window_dataset  # dataset root dir
train: images/train  # train images
val: images/val  # val images
test: images/test  # test images (optional)

# Classes
names:
  0: door
  1: window

# Number of classes
nc: 2
"""
    
    os.makedirs("data", exist_ok=True)
    with open("data/doors_windows.yaml", "w") as f:
        f.write(yaml_content)
    
    print("✓ Sample data.yaml created at: data/doors_windows.yaml")
    print("\n📝 Instructions:")
    print("1. Collect images of rooms with doors and windows")
    print("2. Annotate using Roboflow/LabelImg")
    print("3. Export in YOLOv8 format")
    print("4. Update the 'path' in data/doors_windows.yaml")
    print("5. Run: python scripts/train_detector.py")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train YOLO detector for doors and windows")
    parser.add_argument("--data", type=str, default="data/doors_windows.yaml",
                        help="Path to data YAML file")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Number of training epochs")
    parser.add_argument("--img-size", type=int, default=640,
                        help="Image size for training")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size")
    parser.add_argument("--create-yaml", action="store_true",
                        help="Create sample data.yaml")
    
    args = parser.parse_args()
    
    if args.create_yaml:
        create_sample_data_yaml()
    else:
        if not os.path.exists(args.data):
            print(f"❌ Data YAML not found: {args.data}")
            print("Run with --create-yaml to create a sample configuration")
        else:
            train_detector(
                data_yaml=args.data,
                epochs=args.epochs,
                img_size=args.img_size,
                batch_size=args.batch
            )
