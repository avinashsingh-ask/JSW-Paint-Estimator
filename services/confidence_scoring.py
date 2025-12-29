"""Confidence scoring and error estimation for CV measurements."""
import numpy as np
from typing import Dict, List, Optional


class ConfidenceScoring:
    """
    Calculate confidence scores and expected errors for CV-based measurements.
    
    Provides transparent uncertainty quantification to users.
    """
    
    def __init__(self):
        """Initialize confidence scoring service."""
        pass
    
    def calculate_scale_confidence(
        self,
        scale_inference_result: Dict
    ) -> float:
        """
        Calculate confidence in scale estimation.
        
        Args:
            scale_inference_result:  Result from ScaleInference.infer_scale()
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        base_confidence = scale_inference_result.get('confidence', 0.0)
        candidates_count = scale_inference_result.get('candidates_count', 0)
        
        # Boost confidence with more candidates (diminishing returns)
        multi_candidate_boost = min(0.2, candidates_count * 0.05)
        
        final_confidence = min(1.0, base_confidence + multi_candidate_boost)
        
        return float(final_confidence)
    
    def calculate_dimension_confidence(
        self,
        scale_confidence: float,
        estimation_method: str
    ) -> float:
        """
        Calculate confidence in dimension measurements.
        
        Args:
            scale_confidence: Confidence in scale estimation
            estimation_method: Method used (video_multi_frame, single_image, etc.)
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        # Base confidence from scale
        confidence = scale_confidence
        
        # Boost for better methods
        method_multipliers = {
            'vision_api': 1.0,           # Best: AI vision
            'video_multi_frame': 0.95,   # Very good: multiple frames
            'cv_estimation': 0.85,       # Good: single frame CV
            'manual_input': 1.0,         # Perfect: user provided
            'default_assumption': 0.3    # Poor: fallback guess
        }
        
        multiplier = method_multipliers.get(estimation_method, 0.7)
        confidence *= multiplier
        
        return float(min(1.0, confidence))
    
    def calculate_overall_confidence(
        self,
        scale_confidence: float,
        dimension_confidence: float,
        detection_confidence: float
    ) -> float:
        """
        Calculate overall estimation confidence.
        
        Args:
            scale_confidence: Confidence in scale
            dimension_confidence: Confidence in dimensions
            detection_confidence: Confidence in object detection
        
        Returns:
            Overall confidence (0.0 - 1.0)
        """
        # Geometric mean of all confidences
        confidences = [scale_confidence, dimension_confidence, detection_confidence]
        overall = np.prod(confidences) ** (1 / len(confidences))
        
        return float(overall)
    
    def estimate_error_percentage(
        self,
        confidence: float
    ) -> float:
        """
        Estimate expected error percentage from confidence.
        
        Args:
            confidence: Confidence score (0.0 - 1.0)
        
        Returns:
            Expected error percentage (e.g., 15.0 means ±15%)
        """
        if confidence >= 0.95:
            return 5.0   # ±5% for very high confidence
        elif confidence >= 0.85:
            return 10.0  # ±10%
        elif confidence >= 0.75:
            return 15.0  # ±15%
        elif confidence >= 0.60:
            return 20.0  # ±20%
        else:
            return 30.0  # ±30% for low confidence
    
    def get_confidence_level(
        self,
        confidence: float
    ) -> str:
        """
        Convert confidence score to human-readable level.
        
        Args:
            confidence: Confidence score (0.0 - 1.0)
        
        Returns:
            Confidence level string
        """
        if confidence >= 0.90:
            return "Very High"
        elif confidence >= 0.75:
            return "High"
        elif confidence >= 0.60:
            return "Medium"
        elif confidence >= 0.40:
            return "Low"
        else:
            return "Very Low"
    
    def generate_confidence_report(
        self,
        scale_confidence: float,
        dimension_confidence: float,
        detection_confidence: float,
        estimation_mode: str
    ) -> Dict:
        """
        Generate comprehensive confidence report.
        
        Args:
            scale_confidence: Scale estimation confidence
            dimension_confidence: Dimension measurement confidence
            detection_confidence: Object detection confidence
            estimation_mode: Estimation method used
        
        Returns:
            Dictionary with confidence metrics
        """
        overall_confidence = self.calculate_overall_confidence(
            scale_confidence,
            dimension_confidence,
            detection_confidence
        )
        
        expected_error = self.estimate_error_percentage(overall_confidence)
        
        confidence_level = self.get_confidence_level(overall_confidence)
        
        return {
            'overall_confidence': round(overall_confidence, 3),
            'confidence_level': confidence_level,
            'expected_error_percent': expected_error,
            'estimation_mode': estimation_mode,
            'breakdown': {
                'scale_confidence': round(scale_confidence, 3),
                'dimension_confidence': round(dimension_confidence, 3),
                'detection_confidence': round(detection_confidence, 3)
            }
        }
    
    def should_request_manual_input(
        self,
        overall_confidence: float,
        threshold: float = 0.4
    ) -> bool:
        """
        Determine if manual input should be requested.
        
        Args:
            overall_confidence: Overall confidence score
            threshold: Minimum acceptable confidence
        
        Returns:
            True if manual input needed
        """
        return overall_confidence < threshold
