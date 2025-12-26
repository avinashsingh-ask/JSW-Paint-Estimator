"""Video processing service for extracting frames and metadata."""
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
import tempfile
import os
from pathlib import Path


class VideoProcessor:
    """Service for processing video files and extracting frames."""
    
    def __init__(
        self,
        max_duration_seconds: int = 30,
        max_file_size_mb: int = 50,
        frame_extraction_fps: float = 2.0
    ):
        """
        Initialize video processor.
        
        Args:
            max_duration_seconds: Maximum allowed video duration
            max_file_size_mb: Maximum allowed file size in MB
            frame_extraction_fps: Frames to extract per second
        """
        self.max_duration = max_duration_seconds
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.frame_extraction_fps = frame_extraction_fps
        
        # Supported video formats
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
    
    def validate_video(self, video_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate video file.
        
        Args:
            video_bytes: Video file bytes
            filename: Original filename
        
        Returns:
            Validation result dictionary
        
        Raises:
            ValueError: If video is invalid
        """
        # Check file size
        file_size = len(video_bytes)
        if file_size > self.max_file_size:
            raise ValueError(
                f"Video file too large ({file_size / 1024 / 1024:.1f} MB). "
                f"Maximum allowed: {self.max_file_size / 1024 / 1024} MB"
            )
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(
                f"Unsupported video format '{file_ext}'. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
        
        # Verify it's actually a video by trying to open it
        temp_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                tmp.write(video_bytes)
                temp_path = tmp.name
            
            # Open video
            cap = cv2.VideoCapture(temp_path)
            
            if not cap.isOpened():
                raise ValueError("Unable to open video file. File may be corrupted.")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # Check duration
            if duration > self.max_duration:
                raise ValueError(
                    f"Video too long ({duration:.1f} seconds). "
                    f"Maximum allowed: {self.max_duration} seconds"
                )
            
            return {
                "valid": True,
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "resolution": {"width": width, "height": height},
                "file_size": file_size
            }
            
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def extract_frames(
        self,
        video_bytes: bytes,
        filename: str
    ) -> List[np.ndarray]:
        """
        Extract frames from video at specified FPS.
        
        Args:
            video_bytes: Video file bytes
            filename: Original filename
        
        Returns:
            List of frame images as numpy arrays
        """
        temp_path = None
        frames = []
        
        try:
            # Create temporary file
            file_ext = Path(filename).suffix.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                tmp.write(video_bytes)
                temp_path = tmp.name
            
            # Open video
            cap = cv2.VideoCapture(temp_path)
            
            if not cap.isOpened():
                raise ValueError("Unable to open video file")
            
            # Get video properties
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Calculate frame interval
            if video_fps <= 0:
                raise ValueError("Invalid video FPS")
            
            frame_interval = int(video_fps / self.frame_extraction_fps)
            if frame_interval < 1:
                frame_interval = 1
            
            frame_number = 0
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Extract frame at intervals
                if frame_number % frame_interval == 0:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                
                frame_number += 1
            
            cap.release()
            
            if not frames:
                raise ValueError("No frames could be extracted from video")
            
            return frames
            
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def process_video(
        self,
        video_bytes: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Process video: validate and extract frames.
        
        Args:
            video_bytes: Video file bytes
            filename: Original filename
        
        Returns:
            Dictionary with validation metadata and extracted frames
        """
        # Validate video
        validation = self.validate_video(video_bytes, filename)
        
        # Extract frames
        frames = self.extract_frames(video_bytes, filename)
        
        return {
            "metadata": validation,
            "frames": frames,
            "extracted_frame_count": len(frames)
        }
