#!/usr/bin/env python3
"""
Quick setup script to download and install YOLOv8 model for JSW Paint Estimator.
This will fix the "Ran out of input" error.
"""

import os
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("JSW Paint Estimator - YOLO Model Setup")
    print("=" * 60)
    print()
    
    # Check if ultralytics is installed
    try:
        from ultralytics import YOLO
        print("✅ Ultralytics package found")
    except ImportError:
        print("❌ Ultralytics not installed!")
        print("   Installing ultralytics...")
        os.system(f"{sys.executable} -m pip install ultralytics")
        from ultralytics import YOLO
        print("✅ Ultralytics installed successfully")
    
    print()
    
    # Create directory if needed
    model_dir = Path("cv_models/yolo")
    model_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directory created: {model_dir}")
    
    # Check if model already exists and is not empty
    model_path = model_dir / "best.pt"
    if model_path.exists() and model_path.stat().st_size > 0:
        size_mb = model_path.stat().st_size / 1024 / 1024
        print(f"⚠️  Model already exists: {model_path}")
        print(f"   Size: {size_mb:.2f} MB")
        
        response = input("\nOverwrite existing model? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Setup cancelled")
            return
    
    print()
    print("📥 Downloading YOLOv8n model...")
    print("   This may take a few minutes...")
    
    try:
        # Download YOLOv8 nano model
        model = YOLO('yolov8n.pt')
        
        # Save to project directory
        model.save(str(model_path))
        
        # Verify file size
        size_mb = model_path.stat().st_size / 1024 / 1024
        
        print()
        print("=" * 60)
        print("✅ SUCCESS! YOLO model installed")
        print("=" * 60)
        print(f"   Location: {model_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print()
        print("🎯 Next Steps:")
        print("   1. Restart your backend server")
        print("   2. Check model status: curl http://localhost:8000/api/v1/estimate/cv/model-status")
        print("   3. Test image upload via frontend or API")
        print()
        print("⚠️  Note: YOLOv8n is a general-purpose model, not trained")
        print("   specifically for doors/windows. For better accuracy,")
        print("   consider training a custom model.")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR during model download")
        print("=" * 60)
        print(f"   Error: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   - Check your internet connection")
        print("   - Ensure you have write permissions")
        print("   - Try manually downloading from:")
        print("     https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt")
        sys.exit(1)

if __name__ == "__main__":
    main()
