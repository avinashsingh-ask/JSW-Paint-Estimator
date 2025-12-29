"""LLM Validation Layer for geometry and dimension validation.

Uses existing Gemini/OpenAI services to validate detected dimensions
and reject physically impossible measurements.
"""
from typing import Dict, List, Optional, Any
import json


class LLMValidator:
    """
    Validates room dimensions and geometry using LLM reasoning.
    
    The LLM acts as a validator, NOT a measurer. It:
    - Checks if dimensions are physically plausible
    - Ranks reference objects by reliability
    - Detects contradictory scale hypotheses
    - Infers room type for better validation
    """
    
    def __init__(self):
        """Initialize LLM validator with existing services."""
        self.gemini_ocr = None
        self.azure_openai_ocr = None
        
        # Try to load existing LLM services
        try:
            from services.gemini_ocr import GeminiOCR
            self.gemini_ocr = GeminiOCR()
            if self.gemini_ocr.is_available():
                print("✅ LLM Validator: Gemini available")
        except Exception as e:
            print(f"⚠️  Gemini not available for validation: {e}")
        
        try:
            from services.azure_openai_ocr import AzureOpenAIOCR
            self.azure_openai_ocr = AzureOpenAIOCR()
            if self.azure_openai_ocr.is_available():
                print("✅ LLM Validator: Azure OpenAI available (fallback)")
        except Exception as e:
            print(f"⚠️  Azure OpenAI not available for validation: {e}")
    
    def is_available(self) -> bool:
        """Check if LLM validation is available."""
        return (self.gemini_ocr is not None and self.gemini_ocr.is_available()) or \
               (self.azure_openai_ocr is not None and self.azure_openai_ocr.is_available())
    
    def validate_dimensions(
        self,
        dimensions: Dict[str, float],
        room_type: Optional[str] = None,
        detected_objects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate room dimensions using LLM reasoning.
        
        Args:
            dimensions: {length, width, height} in feet
            room_type: Optional room type hint
            detected_objects: List of detected objects
        
        Returns:
            Validation result with plausibility score and reasoning
        """
        if not self.is_available():
            return {
                'is_valid': True,
                'confidence': 0.5,
                'reasoning': 'LLM validation not available',
                'warnings': []
            }
        
        # Build validation prompt
        prompt = self._build_validation_prompt(dimensions, room_type, detected_objects)
        
        # Call LLM
        try:
            result = self._call_llm(prompt)
            return self._parse_validation_response(result)
        except Exception as e:
            print(f"⚠️  LLM validation error: {e}")
            return {
                'is_valid': True,
                'confidence': 0.5,
                'reasoning': f'Validation error: {str(e)}',
                'warnings': []
            }
    
    def rank_reference_objects(
        self,
        detected_objects: List[Dict],
        room_context: Optional[str] = None
    ) -> List[Dict]:
        """
        Rank detected objects by reliability as reference objects.
        
        Args:
            detected_objects: List of {class_name, confidence, bbox}
            room_context: Optional context about the room
        
        Returns:
            Objects ranked by reliability score
        """
        if not self.is_available():
            # Fallback: simple rule-based ranking
            reliability_map = {
                'door': 0.9,
                'window': 0.7,
                'person': 0.6,
                'switchboard': 0.5,
                'tile': 0.4
            }
            
            for obj in detected_objects:
                obj['reliability'] = reliability_map.get(obj.get('class_name', '').lower(), 0.3)
            
            return sorted(detected_objects, key=lambda x: x['reliability'], reverse=True)
        
        # Use LLM for intelligent ranking
        prompt = self._build_ranking_prompt(detected_objects, room_context)
        
        try:
            result = self._call_llm(prompt)
            return self._parse_ranking_response(result, detected_objects)
        except Exception as e:
            print(f"⚠️  Object ranking error: {e}")
            # Fallback to simple ranking
            return detected_objects
    
    def detect_contradictions(
        self,
        scale_candidates: List[Dict]
    ) -> Dict[str, Any]:
        """
        Detect contradictory scale hypotheses.
        
        Args:
            scale_candidates: List of scale estimates from different objects
        
        Returns:
            Contradiction detection result
        """
        if len(scale_candidates) < 2:
            return {'has_contradictions': False, 'reasoning': 'Not enough candidates'}
        
        # Calculate variance
        scales = [c['scale'] for c in scale_candidates]
        mean_scale = sum(scales) / len(scales)
        variance = sum((s - mean_scale) ** 2 for s in scales) / len(scales)
        std_dev = variance ** 0.5
        
        # High variance = potential contradiction
        coefficient_of_variation = std_dev / mean_scale if mean_scale > 0 else 0
        
        if coefficient_of_variation > 0.3:  # 30% variation
            return {
                'has_contradictions': True,
                'reasoning': f'High variance in scale estimates (CV: {coefficient_of_variation:.2f})',
                'recommendation': 'manual_verification',
                'variance': variance,
                'std_dev': std_dev
            }
        
        return {
            'has_contradictions': False,
            'reasoning': 'Scale estimates are consistent',
            'variance': variance,
            'std_dev': std_dev
        }
    
    def _build_validation_prompt(
        self,
        dimensions: Dict[str, float],
        room_type: Optional[str],
        detected_objects: Optional[List[str]]
    ) -> str:
        """Build LLM prompt for dimension validation."""
        objects_str = ', '.join(detected_objects) if detected_objects else 'unknown'
        room_str = room_type or 'unknown'
        
        prompt = f"""You are a construction expert validating room dimensions.

Room Details:
- Type: {room_str}
- Detected Objects: {objects_str}
- Measured Dimensions:
  * Length: {dimensions.get('length', 0):.1f} feet
  * Width: {dimensions.get('width', 0):.1f} feet
  * Height: {dimensions.get('height', 0):.1f} feet

Analyze these dimensions and respond in JSON format:
{{
  "is_plausible": true/false,
  "confidence": 0-1,
  "reasoning": "brief explanation",
  "warnings": ["list", "of", "warnings"],
  "suggested_corrections": {{"field": "corrected_value"}}
}}

Consider:
1. Are these dimensions physically reasonable for this room type?
2. Is the aspect ratio realistic?
3. Is the ceiling height appropriate?
4. Do the dimensions match the detected objects?

Respond only with valid JSON."""
        
        return prompt
    
    def _build_ranking_prompt(
        self,
        objects: List[Dict],
        context: Optional[str]
    ) -> str:
        """Build LLM prompt for object reliability ranking."""
        objects_list = [f"- {obj.get('class_name', 'unknown')} (confidence: {obj.get('confidence', 0):.2f})" 
                        for obj in objects]
        objects_str = '\n'.join(objects_list)
        
        prompt = f"""Rank these detected objects by reliability as measurement references.

Context: {context or 'General room'}

Detected Objects:
{objects_str}

Respond in JSON format with reliability scores (0-1):
{{
  "rankings": [
    {{"object": "door", "reliability": 0.9, "reason": "Standard size"}},
    ...
  ]
}}

Consider:
1. Size standardization (doors > windows > furniture)
2. Visual clarity and occlusion
3. Detection confidence
4. Context appropriateness

Respond only with valid JSON."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM service (Gemini or OpenAI)."""
        # Try Gemini first
        if self.gemini_ocr and self.gemini_ocr.is_available():
            try:
                # Use Gemini's text generation (not vision)
                import google.generativeai as genai
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini LLM call failed: {e}")
        
        # Fallback to OpenAI
        if self.azure_openai_ocr and self.azure_openai_ocr.is_available():
            try:
                from openai import AzureOpenAI
                client = self.azure_openai_ocr.client
                
                response = client.chat.completions.create(
                    model=self.azure_openai_ocr.deployment_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI LLM call failed: {e}")
        
        raise Exception("No LLM service available")
    
    def _parse_validation_response(self, response: str) -> Dict:
        """Parse LLM validation response."""
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                
                return {
                    'is_valid': data.get('is_plausible', True),
                    'confidence': data.get('confidence', 0.5),
                    'reasoning': data.get('reasoning', ''),
                    'warnings': data.get('warnings', []),
                    'suggested_corrections': data.get('suggested_corrections', {})
                }
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
        
        # Fallback
        return {
            'is_valid': True,
            'confidence': 0.5,
            'reasoning': 'Could not parse LLM response',
            'warnings': []
        }
    
    def _parse_ranking_response(
        self,
        response: str,
        original_objects: List[Dict]
    ) -> List[Dict]:
        """Parse LLM ranking response."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                
                rankings = data.get('rankings', [])
                
                # Match rankings to original objects
                for obj in original_objects:
                    obj_name = obj.get('class_name', '').lower()
                    for rank in rankings:
                        if rank.get('object', '').lower() == obj_name:
                            obj['reliability'] = rank.get('reliability', 0.5)
                            obj['reliability_reason'] = rank.get('reason', '')
                            break
                    
                    # Default if not found
                    if 'reliability' not in obj:
                        obj['reliability'] = 0.5
                
                return sorted(original_objects, key=lambda x: x.get('reliability', 0), reverse=True)
        except Exception as e:
            print(f"Failed to parse ranking response: {e}")
        
        return original_objects
