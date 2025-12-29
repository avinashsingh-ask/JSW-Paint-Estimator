"""Google Gemini API service for intelligent floor plan analysis."""
import os
import base64
import cv2
import numpy as np
from typing import Dict, Any, List
from dotenv import load_dotenv
import json

load_dotenv()


class GeminiOCR:
    """Google Gemini API service for floor plan dimension extraction."""
    
    def __init__(self):
        """Initialize Google Gemini client."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("⚠️  Gemini API key not found in .env")
            self.client = None
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                
                # Use Gemini 2.5 Flash (faster, less strict safety filters)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.client = genai
                print("✅ Google Gemini 2.5 Flash initialized (PRIMARY OCR - Fast & Accurate)")
            except ImportError:
                print("⚠️  google-generativeai package not found. Install with: pip install google-generativeai")
                self.client = None
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return self.client is not None
    
    def _encode_image(self, image: np.ndarray) -> bytes:
        """
        Encode image to bytes for Gemini.
        
        Args:
            image: Image as numpy array
        
        Returns:
            Image bytes
        """
        # Convert to PNG
        success, buffer = cv2.imencode('.png', image)
        if not success:
            raise ValueError("Failed to encode image")
        
        return buffer.tobytes()
    
    def extract_dimensions(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract room dimensions from floor plan using Gemini Vision.
        
        Args:
            image: Floor plan image
        
        Returns:
            Dictionary with extracted dimensions and room labels
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Gemini not initialized',
                'text': '',
                'text_boxes': [],
                'dimensions': [],
                'room_labels': []
            }
        
        try:
            print("\n🤖 [GEMINI] Using Gemini 2.5 Flash for intelligent floor plan analysis...")
            
            # Encode image
            image_bytes = self._encode_image(image)
            
            # Create enhanced prompt for Gemini with validation
            prompt = """You are an expert architectural floor plan analyst. Your task is to extract room dimensions with EXTREME ACCURACY.

INSTRUCTIONS:
1. Carefully examine EVERY room in the floor plan
2. Find the dimension annotations for each room (format: 15'9" × 10'0" or similar)
3. Identify the room label/name near each room
4. Convert dimensions to decimal feet accurately

CRITICAL RULES FOR ACCURACY:
- Read dimensions EXACTLY as shown - do NOT confuse nearby numbers
- Common garage size: 10-25 feet wide (NOT 30+ feet)
- Living rooms: typically 15-30 feet in each dimension
- Bedrooms: typically 10-15 feet in each dimension
- Kitchens: typically 10-20 feet in each dimension
- If a dimension seems wrong (e.g., 2 feet or 50+ feet), double-check!

CONVERSION RULES:
- 1 inch = 0.083 feet (1/12)
- Examples:
  * 15'9" = 15 + (9/12) = 15.75 feet
  * 13'2" = 13 + (2/12) = 13.17 feet
  * 10'10" = 10 + (10/12) = 10.83 feet

VALIDATION:
- Garage width should be 10-25 feet typically
- No room dimension should be < 5 feet or > 50 feet
- If you see conflicting numbers, choose the one closest to the room

Return ONLY valid JSON in this EXACT format:
{
  "rooms": [
    {
      "name": "Exact room name from floor plan (e.g., 'Living Room', 'Garage', 'Master Bedroom')",
      "dimensions_text": "Exact dimension string as shown (e.g., '15\\'9\\" × 10\\'0\\\"')",
      "length_feet": 15.75,
      "width_feet": 10.00,
      "confidence": 0.95,
      "notes": "Any observations about this room"
    }
  ]
}

IMPORTANT: 
- Return dimensions in the order: length × width (as shown on plan)
- Use confidence 0.9+ for clear dimensions, 0.7-0.9 for unclear
- In 'notes', mention if dimension was hard to read or if you made assumptions
- Extract EVERY room with visible dimensions
- ONLY return valid JSON, no markdown code blocks or extra text
"""
            
            # Prepare image for Gemini
            import PIL.Image
            import io
            pil_image = PIL.Image.open(io.BytesIO(image_bytes))
            
            # Call Gemini Vision with relaxed safety settings for architectural drawings
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
            ]
            
            response = self.model.generate_content(
                [prompt, pil_image],
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistent extraction
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 8192,  # Maximum allowed for complete responses
                    'candidate_count': 1,  # Single response
                },
                safety_settings=safety_settings,
                stream=False  # Force complete response, not streaming
            )
            
            # Check if response was generated successfully
            if not response.candidates:
                raise ValueError("No response candidates generated")
            
            candidate = response.candidates[0]
            
            # Check finish reason
            finish_reason = candidate.finish_reason
            print(f"   🏁 Finish reason: {finish_reason}")
            
            if finish_reason == 1:  # STOP - normal completion
                print(f"   ✅ Response completed normally")
            elif finish_reason == 2:  # MAX_TOKENS
                print(f"   ⚠️  Response truncated (hit token limit)")
            elif finish_reason == 3:  # SAFETY
                raise ValueError("Response blocked by safety filters")
            elif finish_reason == 4:  # RECITATION
                raise ValueError("Response blocked due to recitation")
            
            # Parse response
            content = response.text
            print(f"\n📝 Gemini Response Preview:")
            print(content[:500])
            
            # Parse JSON
            try:
                # Remove markdown code blocks if present
                content_clean = content
                if '```json' in content:
                    # Extract content between ```json and ```
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    if end > start:
                        content_clean = content[start:end].strip()
                        print(f"   📋 Extracted from ```json block")
                elif '```' in content:
                    # Generic code block
                    start = content.find('```') + 3
                    end = content.find('```', start)
                    if end > start:
                        content_clean = content[start:end].strip()
                        print(f"   📋 Extracted from ``` block")
                
                # Extract JSON from response
                json_start = content_clean.find('{')
                json_end = content_clean.rfind('}') + 1
                
                print(f"   🔍 JSON positions: start={json_start}, end={json_end}")
                print(f"   📏 Content length: {len(content_clean)}")
                
                if json_start == -1:
                    raise ValueError(f"No opening brace found. Content preview: {content_clean[:200]}")
                if json_end == 0:
                    raise ValueError(f"No closing brace found. Content preview: {content_clean[:200]}")
                
                json_str = content_clean[json_start:json_end]
                print(f"   ✂️  JSON string length: {len(json_str)}")
                
                result = json.loads(json_str)
                rooms_data = result.get('rooms', [])
                
                
                print(f"\n✅ Gemini extracted {len(rooms_data)} rooms")
                
                # STEP 1: DUPLICATE DETECTION
                # Check for rooms with identical or very similar dimensions
                print(f"\n🔍 Checking for duplicate rooms...")
                unique_rooms = []
                duplicates_removed = []
                
                for i, room in enumerate(rooms_data):
                    length = room.get('length_feet', 0)
                    width = room.get('width_feet', 0)
                    name = room.get('name', f'Room {i+1}')
                    
                    # Check if this room is a duplicate
                    is_duplicate = False
                    for existing_room in unique_rooms:
                        existing_length = existing_room.get('length_feet', 0)
                        existing_width = existing_room.get('width_feet', 0)
                        
                        # Check if dimensions match (within 0.5 ft tolerance)
                        length_match = abs(length - existing_length) < 0.5 and abs(width - existing_width) < 0.5
                        # Also check if dimensions are swapped
                        swapped_match = abs(length - existing_width) < 0.5 and abs(width - existing_length) < 0.5
                        
                        if length_match or swapped_match:
                            is_duplicate = True
                            existing_name = existing_room.get('name', 'Unknown')
                            duplicates_removed.append({
                                'name': name,
                                'dimensions': f"{length}' × {width}'",
                                'duplicate_of': existing_name
                            })
                            print(f"   ⚠️  DUPLICATE FOUND: '{name}' ({length}' × {width}') matches '{existing_name}'")
                            break
                    
                    if not is_duplicate:
                        unique_rooms.append(room)
                
                if duplicates_removed:
                    print(f"\n🔧 Removed {len(duplicates_removed)} duplicate room(s)")
                    for dup in duplicates_removed:
                        print(f"   - '{dup['name']}' (duplicate of '{dup['duplicate_of']}')")
                    rooms_data = unique_rooms
                    print(f"   ✅ Final room count: {len(rooms_data)} (was {len(rooms_data) + len(duplicates_removed)})")
                else:
                    print(f"   ✅ No duplicates found")
                
                # VALIDATION: Check for unrealistic dimensions
                validated_rooms = []
                for room in rooms_data:
                    room_name = room.get('name', '')
                    length = room.get('length_feet', 0)
                    width = room.get('width_feet', 0)
                    
                    # Validation flags
                    warnings = []
                    
                    # Check for unrealistic dimensions
                    if length < 5 or width < 5:
                        warnings.append(f"⚠️  Suspiciously small ({length}' × {width}')")
                    if length > 50 or width > 50:
                        warnings.append(f"⚠️  Suspiciously large ({length}' × {width}')")
                    
                    # Room-specific validation
                    if 'garage' in room_name.lower():
                        # Garages can vary significantly in shape:
                        # - Single car: ~10-12' wide × 18-24' deep
                        # - Double car: ~18-24' wide × 18-24' deep  
                        # - Deep garage: ~15' wide × 30' deep (for storage/workspace)
                        # DO NOT auto-swap - trust the floor plan dimensions as-is
                        
                        # Just validate garage is reasonable size (not checking which is larger)
                        if width > 35 or length > 35:
                            warnings.append(f"⚠️  Garage dimension {length}' × {width}' seems unusually large")
                        elif width < 8 or length < 15:
                            warnings.append(f"⚠️  Garage dimension {length}' × {width}' seems small for a garage")

                    
                    if 'bedroom' in room_name.lower():
                        if length > 20 or width > 20:
                            warnings.append(f"⚠️  Bedroom seems large ({length}' × {width}')")
                    
                    if warnings:
                        print(f"\n🔍 Validation for {room_name}:")
                        for warning in warnings:
                            print(f"   {warning}")
                    
                    validated_rooms.append(room)
                
                # FIX #3: Room Count & Name Validation
                print(f"\n📊 Final Validation Summary:")
                print(f"   Total rooms after validation: {len(validated_rooms)}")
                
                # Warn if unusually high room count
                if len(validated_rooms) > 10:
                    print(f"   ⚠️  WARNING: {len(validated_rooms)} rooms seems high for a typical house")
                
                # Check for suspicious room names/sizes
                for room in validated_rooms:
                    name = room.get('name', '').lower()
                    length = room.get('length_feet', 0)
                    width = room.get('width_feet', 0)
                    area = length * width
                    
                    # Balcony/patio that's too small might be closet
                    if 'balcony' in name or 'patio' in name:
                        if area < 100:
                            print(f"   💡 Note: '{room.get('name')}' ({length}' x {width}') might be a closet/storage")
                
                # Convert to our format
                dimensions = []
                room_labels = []
                text_boxes = []
                
                for i, room in enumerate(validated_rooms):
                    # Create dimension entry
                    dimensions.append({
                        'raw_text': room.get('dimensions_text', ''),
                        'length': room.get('length_feet', 0),
                        'width': room.get('width_feet', 0),
                        'format': 'gemini_vision',
                        'confidence': room.get('confidence', 0.9)
                    })
                    
                    # Create room label entry
                    room_labels.append({
                        'label': room.get('name', f'Room {i+1}'),
                        'keyword': room.get('name', '').lower().split()[0] if room.get('name') else '',
                        'confidence': room.get('confidence', 0.9) * 100,
                        'bbox': {'x': 0, 'y': 0, 'w': 100, 'h': 100}  # Dummy bbox
                    })
                    
                    # Create text box for compatibility
                    text_boxes.append({
                        'text': f"{room.get('name', '')} {room.get('dimensions_text', '')}",
                        'confidence': room.get('confidence', 0.9) * 100,
                        'bbox': {'x': 0, 'y': 0, 'w': 100, 'h': 100}
                    })
                
                return {
                    'text': content,
                    'text_boxes': text_boxes,
                    'dimensions': dimensions,
                    'room_labels': room_labels,
                    'total_text_regions': len(text_boxes),
                    'total_dimensions_found': len(dimensions),
                    'total_rooms_found': len(room_labels),
                    'ocr_engine': 'google_gemini_2.5_pro'
                }
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse JSON response: {e}")
                print(f"   Response: {content}")
                return {
                    'success': False,
                    'error': f'JSON parse error: {e}',
                    'text': content,
                    'text_boxes': [],
                    'dimensions': [],
                    'room_labels': []
                }
        
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'text_boxes': [],
                'dimensions': [],
                'room_labels': []
            }

    def analyze_room_photo(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze a real room photograph to estimate dimensions.
        
        This method is designed for actual room photos (from videos or single wall uploads),
        NOT for floor plan diagrams. It estimates dimensions from visual cues rather than
        looking for annotation text.
        
        Args:
            image: Room photograph as numpy array
        
        Returns:
            Dictionary with estimated dimensions and detected features
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Gemini not initialized',
                'dimensions': [],
                'objects': {'doors': 0, 'windows': 0},
                'total_dimensions_found': 0
            }
        
        try:
            print("\n🤖 [GEMINI PHOTO] Analyzing room photograph for dimension estimation...")
            
            # Encode image
            image_bytes = self._encode_image(image)
            
            # Create photo-specific prompt
            prompt = """You are an expert interior space analyst. Analyze this photograph of a room and estimate its dimensions.

INSTRUCTIONS:
1. Carefully examine all visible features in this room photograph
2. Identify reference objects (doors, windows, furniture) for scale
3. Estimate the room dimensions based on visual perspective and known object sizes
4. Count doors and windows visible in the image

REFERENCE MEASUREMENTS FOR SCALE:
- Standard door: 7 feet (84 inches) tall, 3 feet (36 inches) wide
- Standard window: typically 3-5 feet tall, 2-4 feet wide  
- Ceiling height: typically 8-10 feet in residential spaces
- Floor tiles (if visible): usually 12 inches (1 foot) square

ANALYSIS APPROACH:
1. Identify the room type (bedroom, living room, kitchen, etc.)
2. Locate any doors and use them as height reference (7 feet)
3. Use perspective lines to estimate depth and width
4. Consider typical room proportions for the room type

TYPICAL ROOM DIMENSIONS:
- Bedroom: 10-15 feet × 10-15 feet
- Living Room: 12-20 feet × 15-25 feet
- Kitchen: 10-15 feet × 10-20 feet
- Bathroom: 5-10 feet × 5-10 feet
- Garage: 12-24 feet × 18-24 feet

Return ONLY valid JSON in this EXACT format:
{
  "room_type": "bedroom/living_room/kitchen/bathroom/other",
  "estimated_dimensions": {
    "length_feet": 15.0,
    "width_feet": 12.0,
    "height_feet": 9.0,
    "confidence": 0.75,
    "method": "visual_estimation_with_door_reference"
  },
  "detected_features": {
    "doors_count": 1,
    "windows_count": 2,
    "reference_objects_used": ["door", "window"]
  },
  "notes": "Brief explanation of how you estimated the dimensions"
}

IMPORTANT:
- Use confidence 0.70-0.85 for photo-based estimates (lower than floor plan annotations)
- In 'method', describe what reference objects you used (e.g., "door_reference", "perspective_analysis")
- Be conservative with estimates - it's better to underestimate slightly
- If you can't confidently estimate, return lower confidence (0.60-0.70)
- ONLY return valid JSON, no markdown code blocks or extra text
"""
            
            # Prepare image for Gemini
            import PIL.Image
            import io
            pil_image = PIL.Image.open(io.BytesIO(image_bytes))
            
            # Call Gemini Vision
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
            ]
            
            response = self.model.generate_content(
                [prompt, pil_image],
                generation_config={
                    'temperature': 0.3,  # Slightly higher for estimation tasks
                    'top_p': 0.9,
                    'top_k': 40,
                    'max_output_tokens': 4096,  # Increased to prevent truncation
                    'candidate_count': 1,
                },
                safety_settings=safety_settings,
                stream=False
            )
            
            # Check response
            if not response.candidates:
                raise ValueError("No response candidates generated")
            
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            
            if finish_reason == 3:  # SAFETY
                raise ValueError("Response blocked by safety filters")
            
            # Parse response
            content = response.text
            print(f"\n📝 Gemini Photo Analysis Response Preview:")
            print(content[:400] if len(content) > 400 else content)
            
            # Parse JSON
            try:
                # Remove markdown code blocks if present
                content_clean = content.strip()
                if '```json' in content:
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    if end > start:
                        content_clean = content[start:end].strip()
                elif '```' in content:
                    start = content.find('```') + 3
                    end = content.find('```', start)
                    if end > start:
                        content_clean = content[start:end].strip()
                
                # Extract JSON - find complete JSON object
                json_start = content_clean.find('{')
                json_end = content_clean.rfind('}') + 1
                
                if json_start == -1:
                    raise ValueError(f"No opening brace found. Response may be incomplete. Length: {len(content)}")
                if json_end == 0:
                    raise ValueError(f"No closing brace found. Response may be truncated. Length: {len(content)}")
                
                json_str = content_clean[json_start:json_end]
                result = json.loads(json_str)
                
                # Extract data
                estimated_dims = result.get('estimated_dimensions', {})
                detected_features = result.get('detected_features', {})
                
                length = estimated_dims.get('length_feet', 12.0)
                width = estimated_dims.get('width_feet', 10.0)
                height = estimated_dims.get('height_feet', 9.0)
                confidence = estimated_dims.get('confidence', 0.75)
                
                print(f"\n✅ Gemini Photo Analysis:")
                print(f"   Room Type: {result.get('room_type', 'unknown')}")
                print(f"   Estimated: {length}' × {width}' × {height}'")
                print(f"   Confidence: {confidence * 100:.0f}%")
                print(f"   Doors: {detected_features.get('doors_count', 0)}, Windows: {detected_features.get('windows_count', 0)}")
                print(f"   Notes: {result.get('notes', 'N/A')}")
                
                # Return in compatible format
                return {
                    'success': True,
                    'source_type': 'room_photo',
                    'dimensions': [{
                        'length': length,
                        'width': width,
                        'height': height,
                        'format': 'photo_estimation',
                        'confidence': confidence
                    }],
                    'room_labels': [{
                        'label': result.get('room_type', 'Room'),
                        'keyword': result.get('room_type', 'room'),
                        'confidence': confidence * 100
                    }],
                    'objects': {
                        'doors': detected_features.get('doors_count', 0),
                        'windows': detected_features.get('windows_count', 0)
                    },
                    'total_dimensions_found': 1,
                    'total_rooms_found': 1,
                    'ocr_engine': 'gemini_photo_analysis',
                    'raw_response': result
                }
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse JSON response: {e}")
                return {
                    'success': False,
                    'error': f'JSON parse error: {e}',
                    'dimensions': [],
                    'total_dimensions_found': 0
                }
        
        except Exception as e:
            print(f"❌ Gemini photo analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'dimensions': [],
                'total_dimensions_found': 0
            }

