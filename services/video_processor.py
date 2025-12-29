"""Video processing service for extracting frames and metadata."""
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import os
from pathlib import Path


class VideoProcessor:
    """Service for processing video files and extracting frames."""
    
    def __init__(
        self,
        max_duration_seconds: int = 30,
        max_file_size_mb: int = 50,
        frame_extraction_fps: float = 2.0,
        use_vision_api: bool = True
    ):
        """
        Initialize video processor.
        
        Args:
            max_duration_seconds: Maximum allowed video duration
            max_file_size_mb: Maximum allowed file size in MB
            frame_extraction_fps: Frames to extract per second
            use_vision_api: Use Vision API (Gemini/GPT-4) for frame analysis
        """
        self.max_duration = max_duration_seconds
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.frame_extraction_fps = frame_extraction_fps
        self.use_vision_api = use_vision_api
        
        # Supported video formats
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        
        # Initialize Vision API services if enabled
        self.gemini_ocr = None
        self.azure_openai_ocr = None
        
        if use_vision_api:
            try:
                from services.gemini_ocr import GeminiOCR
                self.gemini_ocr = GeminiOCR()
                if self.gemini_ocr.is_available():
                    print("✅ Video Processing: Gemini Vision API enabled")
            except Exception as e:
                print(f"⚠️  Gemini not available for video: {e}")
            
            try:
                from services.azure_openai_ocr import AzureOpenAIOCR
                self.azure_openai_ocr = AzureOpenAIOCR()
                if self.azure_openai_ocr.is_available():
                    print("✅ Video Processing: Azure OpenAI Vision API enabled (fallback)")
            except Exception as e:
                print(f"⚠️  Azure OpenAI not available for video: {e}")
    
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
        
        # Filter low-quality frames (Phase 2 improvement)
        filtered_frames, quality_scores = self.filter_low_quality_frames(frames)
        
        return {
            "metadata": validation,
            "frames": filtered_frames,
            "extracted_frame_count": len(frames),
            "filtered_frame_count": len(filtered_frames),
            "quality_scores": quality_scores
        }
    
    def analyze_frames_with_vision_api(
        self,
        frames: List[np.ndarray],
        max_frames_to_analyze: int = 3,
        quality_scores: Optional[List[Dict]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Analyze key frames using Vision API (Gemini/GPT-4) to extract dimensions.
        
        Returns ALL results for median aggregation, not just the best one.
        
        Args:
            frames: List of extracted video frames
            max_frames_to_analyze: Maximum number of frames to send to Vision API
            quality_scores: Optional quality scores for each frame
        
        Returns:
            List of dimension extraction results from all analyzed frames, or None if Vision API unavailable
        """
        if not self.use_vision_api or (not self.gemini_ocr and not self.azure_openai_ocr):
            print("⚠️  Vision API not available for video frame analysis")
            return None
        
        # Select key frames to analyze (evenly distributed)
        total_frames = len(frames)
        if total_frames == 0:
            return None
        
        # Select frames at even intervals
        frame_indices = []
        if total_frames <= max_frames_to_analyze:
            frame_indices = list(range(total_frames))
        else:
            step = total_frames / max_frames_to_analyze
            frame_indices = [int(i * step) for i in range(max_frames_to_analyze)]
        
        print(f"\n🎬 Analyzing {len(frame_indices)} key frames with Vision API...")
        
        # Analyze each selected frame - COLLECT ALL RESULTS
        all_results = []
        for idx in frame_indices:
            frame = frames[idx]
            
            # Get quality score for this frame
            quality = None
            if quality_scores and idx < len(quality_scores):
                quality = quality_scores[idx].get('overall_quality', 0)
                
                # Skip low-quality frames (confidence filtering)
                if quality < 60:
                    print(f"\n📸 Frame {idx + 1}/{total_frames} - ⏭️  SKIPPED (quality: {quality:.1f}%)")
                    continue
            
            print(f"\n📸 Analyzing frame {idx + 1}/{total_frames}...")
            
            # Try Gemini first
            result = None
            if self.gemini_ocr:
                try:
                    # Use analyze_room_photo for video frames (not floor plans)
                    result = self.gemini_ocr.analyze_room_photo(frame)
                    
                    # Filter by confidence
                    if result.get('total_dimensions_found', 0) > 0:
                        confidence = result['dimensions'][0].get('confidence', 0)
                        if confidence >= 0.6:  # Minimum 60% confidence
                            print(f"   ✅ Gemini found dimensions: {result['dimensions'][0]['length']}' × {result['dimensions'][0]['width']}' (confidence: {confidence:.0%})")
                            result['frame_index'] = idx
                            result['api_used'] = 'gemini'
                            result['frame_quality'] = quality
                            all_results.append(result)
                            continue
                        else:
                            print(f"   ⏭️  Skipped - confidence too low ({confidence:.0%})")
                except Exception as e:
                    print(f"   ⚠️  Gemini error: {e}")
            
            # Fallback to GPT-4
            if self.azure_openai_ocr and not result:
                try:
                    # Use analyze_room_photo for video frames (not floor plans)
                    result = self.azure_openai_ocr.analyze_room_photo(frame)
                    
                    # Filter by confidence
                    if result.get('total_dimensions_found', 0) > 0:
                        confidence = result['dimensions'][0].get('confidence', 0)
                        if confidence >= 0.6:  # Minimum 60% confidence
                            print(f"   ✅ GPT-4 found dimensions: {result['dimensions'][0]['length']}' × {result['dimensions'][0]['width']}' (confidence: {confidence:.0%})")
                            result['frame_index'] = idx
                            result['api_used'] = 'azure_openai'
                            result['frame_quality'] = quality
                            all_results.append(result)
                        else:
                            print(f"   ⏭️  Skipped - confidence too low ({confidence:.0%})")
                except Exception as e:
                    print(f"   ⚠️  GPT-4 error: {e}")
        
        if not all_results:
            print("⚠️  No high-confidence dimensions found in any frames")
            return None
        
        print(f"\n✅ Collected {len(all_results)} high-confidence frame analyses")
        
        # Return ALL results for aggregation
        return all_results
    
    def calculate_frame_quality(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Calculate quality score for a video frame.
        
        Scores based on:
        - Blur (Laplacian variance)
        - Brightness/Contrast
        - Edge density
        
        Args:
            frame: RGB frame as numpy array
        
        Returns:
            Dictionary with quality metrics and overall score
        """
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # 1. Blur detection using Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = laplacian.var()
        normalized_blur = min(100, (blur_score / 200) * 100)
        
        # 2. Brightness and contrast
        mean_brightness = gray.mean()
        std_brightness = gray.std()
        brightness_score = 100 - abs(mean_brightness - 127) / 1.27
        contrast_score = min(100, (std_brightness / 60) * 100)
        
        # 3. Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = (edges > 0).sum() / edges.size
        edge_score = min(100, edge_density * 1000)
        
        # Overall quality (weighted average)
        overall_quality = (
            normalized_blur * 0.4 +
            brightness_score * 0.2 +
            contrast_score * 0.2 +
            edge_score * 0.2
        )
        
        return {
            'blur_score': float(normalized_blur),
            'brightness_score': float(brightness_score),
            'contrast_score': float(contrast_score),
            'edge_score': float(edge_score),
            'overall_quality': float(overall_quality)
        }
    
    def filter_low_quality_frames(
        self,
        frames: List[np.ndarray],
        quality_threshold: float = 40.0
    ) -> Tuple[List[np.ndarray], List[Dict]]:
        """
        Filter out low-quality frames.
        
        Args:
            frames: List of frames
            quality_threshold: Minimum quality score (0-100)
        
        Returns:
            Tuple of (filtered_frames, quality_scores)
        """
        filtered_frames = []
        quality_scores = []
        
        for i, frame in enumerate(frames):
            quality = self.calculate_frame_quality(frame)
            
            if quality['overall_quality'] >= quality_threshold:
                filtered_frames.append(frame)
                quality_scores.append({
                    'frame_index': i,
                    **quality
                })
        
        print(f"\n📊 Frame Quality Filtering:")
        print(f"   Original frames: {len(frames)}")
        print(f"   Filtered frames: {len(filtered_frames)}")
        print(f"   Removed: {len(frames) - len(filtered_frames)} low-quality frames")
        
        return filtered_frames, quality_scores

