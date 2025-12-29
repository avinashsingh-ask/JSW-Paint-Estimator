"""Probabilistic scale inference using statistical object size distributions."""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ObjectSizeDistribution:
    """Statistical distribution for a reference object."""
    mean: float  # Mean size in feet
    std: float   # Standard deviation in feet
    confidence: float  # Prior confidence in this object type


class ScaleInference:
    """
    Probabilistic scale inference engine.
    
    This class implements resolution-invariant, probabilistic scale estimation
    using learned object size distributions instead of fixed constants.
    """
    
    # Indian Standard Object Size Distributions (in feet)
    # Based on Indian Building Code and common residential standards
    OBJECT_DISTRIBUTIONS = {
        "door": ObjectSizeDistribution(
            mean=7.0,      # Standard door height in India
            std=0.5,       # Variance: 6.5ft - 7.5ft range
            confidence=0.9  # High confidence - doors are reliable
        ),
        "window": ObjectSizeDistribution(
            mean=4.0,      # Standard window height
            std=0.8,       # More variance: 3.2ft - 4.8ft range
            confidence=0.7  # Medium confidence - windows vary more
        ),
        "person": ObjectSizeDistribution(
            mean=5.5,      # Average Indian height
            std=0.4,       # Range: 5.1ft - 5.9ft
            confidence=0.6  # Lower confidence - people vary significantly
        ),
        "switchboard": ObjectSizeDistribution(
            mean=0.33,     # ~4 inches (0.33 ft)
            std=0.08,      # Small variance
            confidence=0.5  # Medium-low - small objects less reliable
        ),
        "tile": ObjectSizeDistribution(
            mean=2.0,      # Standard 2ft x 2ft tiles
            std=0.5,       # Some variance
            confidence=0.4  # Low confidence - tiles vary widely
        )
    }
    
    def __init__(self):
        """Initialize scale inference engine."""
        self.distributions = self.OBJECT_DISTRIBUTIONS.copy()
    
    def generate_scale_candidates(
        self,
        detections: List[Dict],
        image_shape: Tuple[int, int]
    ) -> List[Dict]:
        """
        Generate scale candidates from detected objects.
        
        Args:
            detections: List of object detections with bbox and class_name
            image_shape: Original image shape (height, width)
        
        Returns:
            List of scale candidates with confidence scores
        """
        candidates = []
        
        for detection in detections:
            object_type = detection.get('class_name', '').lower()
            bbox = detection.get('bbox', {})
            det_confidence = detection.get('confidence', 1.0)
            
            if object_type not in self.distributions:
                continue
            
            dist = self.distributions[object_type]
            
            # Sample real-world size from distribution
            # For production: use mean; for learning: sample from Normal(μ, σ)
            sampled_real_size = dist.mean
            
            # Get pixel size (use height as primary measure)
            pixel_size = bbox.get('h', 0)
            
            if pixel_size <= 0:
                continue
            
            # Calculate scale: feet per pixel
            scale = sampled_real_size / pixel_size
            
            # Combined confidence = detection confidence × prior confidence
            combined_confidence = det_confidence * dist.confidence
            
            candidates.append({
                'object_type': object_type,
                'scale': scale,
                'confidence': combined_confidence,
                'real_size': sampled_real_size,
                'pixel_size': pixel_size,
                'detection_confidence': det_confidence,
                'prior_confidence': dist.confidence
            })
        
        return candidates
    
    def fuse_scale_candidates(
        self,
        candidates: List[Dict],
        method: str = 'weighted_median'
    ) -> Tuple[float, float]:
        """
        Fuse multiple scale candidates into single estimate.
        
        Args:
            candidates: List of scale candidates with confidence scores
            method: Fusion method ('weighted_median', 'weighted_mean', 'best')
        
        Returns:
            Tuple of (final_scale, confidence)
        """
        if not candidates:
            # No candidates - return None with zero confidence
            return None, 0.0
        
        if len(candidates) == 1:
            # Single candidate
            return candidates[0]['scale'], candidates[0]['confidence']
        
        # Extract scales and confidences
        scales = np.array([c['scale'] for c in candidates])
        confidences = np.array([c['confidence'] for c in candidates])
        
        if method == 'weighted_median':
            # Weighted median - robust to outliers
            sorted_indices = np.argsort(scales)
            sorted_scales = scales[sorted_indices]
            sorted_confidences = confidences[sorted_indices]
            
            cumsum = np.cumsum(sorted_confidences)
            total_weight = cumsum[-1]
            
            # Find median
            median_idx = np.searchsorted(cumsum, total_weight / 2.0)
            final_scale = sorted_scales[median_idx]
            
        elif method == 'weighted_mean':
            # Weighted mean
            final_scale = np.average(scales, weights=confidences)
        
        elif method == 'best':
            # Take highest confidence scale
            best_idx = np.argmax(confidences)
            final_scale = scales[best_idx]
        
        else:
            raise ValueError(f"Unknown fusion method: {method}")
        
        # Overall confidence = mean of candidate confidences
        final_confidence = float(np.mean(confidences))
        
        return float(final_scale), final_confidence
    
    def infer_scale(
        self,
        detections: List[Dict],
        image_shape: Tuple[int, int],
        fusion_method: str = 'weighted_median'
    ) -> Dict:
        """
        Main method: Infer scale from detections.
        
        Args:
            detections: List of object detections
            image_shape: Original image shape (height, width)
            fusion_method: Method to fuse candidates
        
        Returns:
            Dictionary with scale, confidence, and metadata
        """
        # Generate candidates
        candidates = self.generate_scale_candidates(detections, image_shape)
        
        if not candidates:
            return {
                'scale': None,
                'confidence': 0.0,
                'method': 'none',
                'candidates_count': 0,
                'candidates': []
            }
        
        # Fuse candidates
        final_scale, final_confidence = self.fuse_scale_candidates(
            candidates,
            method=fusion_method
        )
        
        return {
            'scale': final_scale,
            'confidence': final_confidence,
            'method': fusion_method,
            'candidates_count': len(candidates),
            'candidates': candidates
        }
    
    def update_distribution(
        self,
        object_type: str,
        observed_size: float,
        weight: float = 0.1
    ):
        """
        Update object size distribution with new observation (learning).
        
        Args:
            object_type: Type of object
            observed_size: Observed real-world size
            weight: Learning rate (0.0 - 1.0)
        """
        if object_type not in self.distributions:
            return
        
        dist = self.distributions[object_type]
        
        # Bayesian update (simple exponential moving average)
        new_mean = (1 - weight) * dist.mean + weight * observed_size
        
        # Update variance estimate
        deviation = abs(observed_size - dist.mean)
        new_std = (1 - weight) * dist.std + weight * deviation
        
        self.distributions[object_type] = ObjectSizeDistribution(
            mean=new_mean,
            std=new_std,
            confidence=dist.confidence
        )
