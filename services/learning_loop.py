"""Learning loop for continuous system improvement.

Stores anonymized estimation results and periodically updates
object size distributions based on real-world data.
"""
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
from datetime import datetime
import hashlib


class LearningLoop:
    """
    Manages the learning loop for continuous improvement.
    
    Stores anonymized results and updates distributions over time.
    """
    
    def __init__(self, data_dir: str = "data/learning"):
        """
        Initialize learning loop.
        
        Args:
            data_dir: Directory to store learning data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.results_file = self.data_dir / "estimation_results.jsonl"
        self.distributions_file = self.data_dir / "distributions_history.json"
        
        print(f"📚 Learning Loop initialized: {self.data_dir}")
    
    def log_result(
        self,
        estimation_data: Dict[str, Any],
        anonymize: bool = True
    ) -> bool:
        """
        Log an estimation result for learning.
        
        Args:
            estimation_data: Full estimation result
            anonymize: Whether to anonymize before storing
        
        Returns:
            Success status
        """
        try:
            # Anonymize if requested
            if anonymize:
                estimation_data = self._anonymize_data(estimation_data)
            
            # Add timestamp
            estimation_data['logged_at'] = datetime.now().isoformat()
            
            # Append to JSONL file
            with open(self.results_file, 'a') as f:
                f.write(json.dumps(estimation_data) + '\n')
            
            print(f"✅ Logged result to learning loop")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to log result: {e}")
            return False
    
    def get_stored_results(
        self,
        limit: Optional[int] = None,
        min_confidence: Optional[float] = None
    ) -> List[Dict]:
        """
        Retrieve stored results for analysis.
        
        Args:
            limit: Maximum number of results to return
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of stored results
        """
        if not self.results_file.exists():
            return []
        
        results = []
        
        try:
            with open(self.results_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        
                        # Filter by confidence if specified
                        if min_confidence is not None:
                            conf = data.get('confidence', {}).get('overall_confidence', 0)
                            if conf < min_confidence:
                                continue
                        
                        results.append(data)
                        
                        # Limit if specified
                        if limit and len(results) >= limit:
                            break
            
            return results
            
        except Exception as e:
            print(f"⚠️  Failed to read results: {e}")
            return []
    
    def update_distributions(
        self,
        scale_inference_service,
        min_data_points: int = 100,
        learning_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        Update object size distributions based on stored data.
        
        Args:
            scale_inference_service: ScaleInference instance to update
            min_data_points: Minimum results before updating
            learning_rate: How much to weight new data (0-1)
        
        Returns:
            Update summary
        """
        # Get high-confidence results
        results = self.get_stored_results(min_confidence=0.75)
        
        if len(results) < min_data_points:
            return {
                'updated': False,
                'reason': f'Not enough data points ({len(results)} < {min_data_points})'
            }
        
        print(f"\n📊 Updating distributions from {len(results)} results...")
        
        # Collect observed sizes by object type
        observations = {}
        
        for result in results:
            # Extract scale candidates
            candidates = result.get('scale_candidates', [])
            
            for candidate in candidates:
                obj_type = candidate.get('object_type')
                real_size = candidate.get('real_size')
                
                if obj_type and real_size:
                    if obj_type not in observations:
                        observations[obj_type] = []
                    observations[obj_type].append(real_size)
        
        # Update each object's distribution
        updates = []
        
        for obj_type, sizes in observations.items():
            if len(sizes) < 10:  # Need at least 10 observations
                continue
            
            # Calculate observed statistics
            observed_mean = sum(sizes) / len(sizes)
            observed_std = (sum((s - observed_mean) ** 2 for s in sizes) / len(sizes)) ** 0.5
            
            # Update distribution with learning rate
            if obj_type in scale_inference_service.distributions:
                old_dist = scale_inference_service.distributions[obj_type]
                
                scale_inference_service.update_distribution(
                    object_type=obj_type,
                    observed_size=observed_mean,
                    weight=learning_rate
                )
                
                new_dist = scale_inference_service.distributions[obj_type]
                
                updates.append({
                    'object_type': obj_type,
                    'old_mean': old_dist.mean,
                    'new_mean': new_dist.mean,
                    'old_std': old_dist.std,
                    'new_std': new_dist.std,
                    'observations': len(sizes)
                })
                
                print(f"   Updated {obj_type}: {old_dist.mean:.2f} → {new_dist.mean:.2f} ft")
        
        # Save update history
        self._save_update_history(updates)
        
        return {
            'updated': True,
            'objects_updated': len(updates),
            'updates': updates,
            'total_results_used': len(results)
        }
    
    def _anonymize_data(self, data: Dict) -> Dict:
        """Remove personally identifiable information."""
        # Create a copy
        anon_data = data.copy()
        
        # Remove any potential PII fields
        pii_fields = ['user_id', 'ip_address', 'email', 'name', 'address']
        for field in pii_fields:
            if field in anon_data:
                # Create hash instead of removing
                if anon_data[field]:
                    anon_data[f'{field}_hash'] = hashlib.sha256(
                        str(anon_data[field]).encode()
                    ).hexdigest()[:16]
                del anon_data[field]
        
        # Remove image data (too large)
        if 'image_data' in anon_data:
            del anon_data['image_data']
        if 'video_data' in anon_data:
            del anon_data['video_data']
        
        return anon_data
    
    def _save_update_history(self, updates: List[Dict]):
        """Save distribution update history."""
        history = []
        
        # Load existing history
        if self.distributions_file.exists():
            try:
                with open(self.distributions_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Add new updates
        history.append({
            'timestamp': datetime.now().isoformat(),
            'updates': updates
        })
        
        # Save
        with open(self.distributions_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_statistics(self) -> Dict:
        """Get learning loop statistics."""
        results = self.get_stored_results()
        
        if not results:
            return {
                'total_results': 0,
                'avg_confidence': 0,
                'estimation_modes': {}
            }
        
        # Calculate statistics
        confidences = [r.get('confidence', {}).get('overall_confidence', 0) for r in results]
        modes = {}
        
        for r in results:
            mode = r.get('estimation_mode', 'unknown')
            modes[mode] = modes.get(mode, 0) + 1
        
        return {
            'total_results': len(results),
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'estimation_modes': modes,
            'high_confidence_ratio': sum(1 for c in confidences if c > 0.75) / len(confidences) if confidences else 0
        }
