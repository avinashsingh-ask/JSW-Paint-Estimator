"""OCR service for extracting text from floor plan images."""
import re
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import pytesseract
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FloorPlanOCR:
    """Service for OCR text extraction from architectural floor plans."""
    
    # Regex patterns for dimension extraction (ordered by specificity)
    DIMENSION_PATTERNS = [
        # Pattern 1: Standard format with feet and inches: 13'2" x 9'1" or 13' 2" x 9' 1"
        # Also handles extra spaces and missing inches
        r"(\d+)\s*['′]\s*(\d+)?\s*[\"″]?\s*[xX×]\s*(\d+)\s*['′]\s*(\d+)?\s*[\"″]?",
        
        # Pattern 2: Handle missing apostrophe before inches: "27 11" x 31' 4"
        r"(\d+)\s+(\d+)\s*[\"″]\s*[xX×]\s*(\d+)\s*['′]\s*(\d+)?\s*[\"″]?",
        
        # Pattern 3: Decimal format: 13.2 x 9.1 or 13 x 9 (whole numbers)
        r"(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)",
        
        # Pattern 4: Hyphen format: 13-2 x 9-1
        r"(\d+)\s*-\s*(\d+)\s*[xX×]\s*(\d+)\s*-\s*(\d+)",
    ]
    
    def __init__(self, confidence_threshold: float = 60.0, use_easyocr: bool = True, use_google_vision: bool = True, use_azure_openai: bool = True, use_gemini: bool = True):
        """
        Initialize OCR service.
        
        Args:
            confidence_threshold: Minimum OCR confidence score (0-100)
            use_easyocr: Use EasyOCR (better for floor plans) if available
            use_google_vision: Use Google Vision API (good for blueprints) if available
            use_azure_openai: Use Azure OpenAI GPT-4 Vision (98% accuracy) if available
            use_gemini: Use Google Gemini 1.5 Pro (PRIMARY - Testing for comparison) if available
        """
        self.confidence_threshold = confidence_threshold
        self.easyocr_reader = None
        self.google_vision = None
        self.azure_openai = None
        self.gemini = None
        self.use_easyocr = use_easyocr
        self.use_google_vision = use_google_vision
        self.use_azure_openai = use_azure_openai
        self.use_gemini = use_gemini
        
        # Priority 1: Try to initialize Gemini (PRIMARY for testing)
        if use_gemini:
            try:
                from services.gemini_ocr import GeminiOCR
                self.gemini = GeminiOCR()
                if self.gemini.is_available():
                    print("✅ Google Gemini 1.5 Pro initialized (PRIMARY OCR - Testing Mode)")
                else:
                    self.gemini = None
            except Exception as e:
                print(f"⚠️  Gemini not available: {e}")
                print("  Falling back to Azure OpenAI...")
                self.gemini = None
        
        # Priority 2: Try to initialize Azure OpenAI GPT-4 Vision (FALLBACK)
        if use_azure_openai:
            try:
                from services.azure_openai_ocr import AzureOpenAIOCR
                self.azure_openai = AzureOpenAIOCR()
                if self.azure_openai.is_available():
                    if self.gemini:
                        print("✅ Azure OpenAI GPT-4 Vision initialized (FALLBACK - 98% accuracy)")
                    else:
                        print("✅ Azure OpenAI GPT-4 Vision initialized (PRIMARY - 98% accuracy)")
                else:
                    self.azure_openai = None
            except Exception as e:
                print(f"⚠️  Azure OpenAI not available: {e}")
                print("  Falling back to Google Vision...")
                self.azure_openai = None
        
        # Priority 3: Try to initialize Google Vision (if Gemini and Azure not available)
        if use_google_vision and not self.gemini and not self.azure_openai:
            try:
                from services.google_vision_ocr import GoogleVisionOCR
                self.google_vision = GoogleVisionOCR()
                if self.google_vision.is_available():
                    print("✅ Google Vision API initialized (FALLBACK OCR - 95% accuracy)")
                else:
                    self.google_vision = None
            except Exception as e:
                print(f"⚠️  Google Vision not available: {e}")
                self.google_vision = None
        
        # Priority 4: Try to initialize EasyOCR (if all AI services not available)
        if use_easyocr and not self.gemini and not self.google_vision and not self.azure_openai:
            try:
                import easyocr
                print("🔍 Initializing EasyOCR (this may take a moment on first run)...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                print("✅ EasyOCR initialized successfully")
            except ImportError:
                print("⚠ EasyOCR not available. Install with: pip install easyocr")
                print("  Falling back to Tesseract OCR")
            except Exception as e:
                print(f"⚠ EasyOCR initialization failed: {e}")
                print("  Falling back to Tesseract OCR")
        
        # Priority 5: Check if tesseract is available (LAST RESORT)
        if not self.gemini and not self.azure_openai and not self.google_vision and not self.easyocr_reader:
            try:
                pytesseract.get_tesseract_version()
                print("✅ Using Tesseract OCR (LAST RESORT)")
            except Exception as e:
                print(f"⚠ Tesseract OCR not available: {e}")
                print("  Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
    
    
    def resize_if_needed(self, image: np.ndarray, max_width: int = 2000) -> np.ndarray:
        """
        Automatically resize large images to prevent memory issues.
        This ensures ANY user upload will work, regardless of size.
        
        Args:
            image: Input image
            max_width: Maximum width in pixels (default: 2000)
        
        Returns:
            Resized image if needed, original if already small enough
        """
        height, width = image.shape[:2]
        
        if width > max_width:
            # Calculate new dimensions maintaining aspect ratio
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            
            print(f"📏 Resizing large image: {width}x{height} → {new_width}x{new_height}")
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized
        else:
            print(f"✅ Image size OK: {width}x{height} (no resize needed)")
            return image
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Advanced preprocessing for architectural floor plans.
        Optimized to avoid memory issues with large images.
        
        Args:
            image: Input image (BGR or grayscale)
        
        Returns:
            Preprocessed image optimized for OCR
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Step 1: Smart upscaling (avoid memory issues)
            height, width = gray.shape
            
            # Only upscale small images
            if width < 1500:
                scale_factor = 2  # Reduced from 3 to save memory
            else:
                scale_factor = 1  # No upscale for larger images
            
            if scale_factor > 1:
                gray = cv2.resize(gray, (width * scale_factor, height * scale_factor), 
                                interpolation=cv2.INTER_CUBIC)
            
            # Step 2: Increase contrast using histogram equalization
            enhanced = cv2.equalizeHist(gray)
            
            # Step 3: Light denoising (reduced to save memory)
            # Use smaller window for faster processing
            try:
                denoised = cv2.fastNlMeansDenoising(enhanced, None, h=7, 
                                                   templateWindowSize=5, 
                                                   searchWindowSize=15)
            except:
                # If denoising fails (memory issue), skip it
                print("⚠️  Skipping denoising (image too large)")
                denoised = enhanced
            
            # Step 4: Adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                10
            )
            
            # Step 5: Light morphological cleanup
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Step 6: Sharpen
            kernel_sharpen = np.array([[-1,-1,-1],
                                       [-1, 9,-1],
                                       [-1,-1,-1]])
            sharpened = cv2.filter2D(cleaned, -1, kernel_sharpen)
            
            return sharpened
            
        except Exception as e:
            print(f"⚠️  Preprocessing error: {e}")
            print("   Falling back to simple preprocessing")
            # Fallback: minimal preprocessing
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
    
    def extract_text_easyocr(
        self,
        image: np.ndarray,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text using EasyOCR (better for floor plans).
        
        Args:
            image: Input image
            preprocess: Whether to preprocess image
        
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.easyocr_reader:
            return self.extract_text(image, preprocess)
        
        # Preprocess if requested
        if preprocess:
            processed_image = self.preprocess_image(image)
        else:
            processed_image = image
        
        try:
            # Run EasyOCR
            results = self.easyocr_reader.readtext(processed_image)
            
            # Convert to our format
            text_boxes = []
            full_text_parts = []
            
            for (bbox, text, confidence) in results:
                # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # Convert to x, y, w, h
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x = int(min(x_coords))
                y = int(min(y_coords))
                w = int(max(x_coords) - x)
                h = int(max(y_coords) - y)
                
                # Convert confidence to 0-100 scale
                conf = confidence * 100
                
                if conf >= self.confidence_threshold and text.strip():
                    text_boxes.append({
                        'text': text.strip(),
                        'confidence': conf,
                        'bbox': {'x': x, 'y': y, 'w': w, 'h': h}
                    })
                    full_text_parts.append(text.strip())
            
            return {
                'text': ' '.join(full_text_parts),
                'text_boxes': text_boxes,
                'total_text_regions': len(text_boxes),
                'ocr_engine': 'easyocr'
            }
        
        except Exception as e:
            print(f"EasyOCR extraction error: {e}")
            print("Falling back to Tesseract...")
            return self.extract_text(image, preprocess)
    
    def extract_text(
        self,
        image: np.ndarray,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extract all text from image using OCR with optimized config for floor plans.
        
        Args:
            image: Input image
            preprocess: Whether to preprocess image
        
        Returns:
            Dictionary with extracted text and metadata
        """
        # Preprocess if requested
        if preprocess:
            processed_image = self.preprocess_image(image)
        else:
            processed_image = image
        
        # Convert to PIL Image for pytesseract
        pil_image = Image.fromarray(processed_image)
        
        # Extract text with detailed data
        try:
            # ChatGPT's recommended config for architectural drawings
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-\'\"()x×'
            
            # Get detailed OCR data with custom config
            ocr_data = pytesseract.image_to_data(
                pil_image,
                output_type=pytesseract.Output.DICT,
                config=custom_config
            )
            
            # Filter by confidence
            text_boxes = []
            for i in range(len(ocr_data['text'])):
                conf = float(ocr_data['conf'][i])
                text = ocr_data['text'][i].strip()
                
                if conf >= self.confidence_threshold and text:
                    text_boxes.append({
                        'text': text,
                        'confidence': conf,
                        'bbox': {
                            'x': ocr_data['left'][i],
                            'y': ocr_data['top'][i],
                            'w': ocr_data['width'][i],
                            'h': ocr_data['height'][i]
                        }
                    })
            
            # Get complete text with custom config
            full_text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            return {
                'text': full_text.strip(),
                'text_boxes': text_boxes,
                'total_text_regions': len(text_boxes)
            }
        
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return {
                'text': '',
                'text_boxes': [],
                'total_text_regions': 0,
                'error': str(e)
            }
    
    def find_dimensions(self, text: str) -> List[Dict[str, Any]]:
        """
        Find dimension patterns in text.
        
        Args:
            text: Input text to search
        
        Returns:
            List of found dimensions with parsed values
        """
        dimensions = []
        print("\n" + "="*80)
        print("🔍 DEBUG: DIMENSION EXTRACTION")
        print("="*80)
        print(f"📝 Full OCR Text ({len(text)} chars):")
        print(text[:500] + "..." if len(text) > 500 else text)
        
        # PRE-PROCESS TEXT TO FIX COMMON OCR ERRORS
        print("\n🔧 PREPROCESSING: Fixing common OCR errors...")
        cleaned_text = self._preprocess_dimension_text(text)
        if cleaned_text != text:
            print("✅ Text was cleaned!")
            print(f"   CHANGED LINES:")
            for i, (orig, clean) in enumerate(zip(text.split('\n'), cleaned_text.split('\n'))):
                if orig != clean:
                    print(f"     Line {i}: '{orig}' -> '{clean}'")
        print("")
        
        for i, pattern in enumerate(self.DIMENSION_PATTERNS):
            print(f"\n🔎 Testing Pattern {i+1}/{len(self.DIMENSION_PATTERNS)}: {pattern}")
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)  # Use cleaned text!
            match_count = 0
            
            for match in matches:
                match_count += 1
                groups = match.groups()
                print(f"  ✓ Match {match_count}: '{match.group(0)}' at position {match.span()}")
                print(f"    Groups: {groups}")
                
                parsed = self._parse_dimension_groups(groups, pattern)
                
                if parsed:
                    print(f"    ✅ Parsed successfully: length={parsed['length']}ft, width={parsed['width']}ft, format={parsed['format']}")
                    dimensions.append({
                        'raw_text': match.group(0),
                        'position': match.span(),
                        'length': parsed['length'],
                        'width': parsed['width'],
                        'format': parsed['format']
                    })
                else:
                    print(f"    ❌ Failed to parse")
            
            if match_count == 0:
                print(f"  ⚠️  No matches found")
        
        print(f"\n📊 TOTAL DIMENSIONS FOUND: {len(dimensions)}")
        for i, dim in enumerate(dimensions):
            print(f"  {i+1}. '{dim['raw_text']}' → {dim['length']}ft × {dim['width']}ft")
        print("="*80 + "\n")
        
        return dimensions
    
    def _preprocess_dimension_text(self, text: str) -> str:
        """
        Preprocess OCR text to fix common errors in dimension strings.
        
        Args:
            text: Raw OCR text
        
        Returns:
            Cleaned text with common OCR errors fixed
        """
        import re
        
        cleaned = text
        
        # Fix 1: Duplicate apostrophes like "13' 2' x" -> "13' 2\" x"
        # Pattern: digit + ' + space + digit + ' + space + x
        cleaned = re.sub(r"(\d+)\s*['′]\s+(\d+)\s*['′]\s+([xX×])", r"\1' \2\" \3", cleaned)
        
        # Fix 2: Missing apostrophe like "27 11\"" -> "27' 11\""
        #Pattern: number + space + number + quote (but NOT after an apostrophe)
        cleaned = re.sub(r"^(\d+)\s+(\d+)\s*[\"″]", r"\1' \2\"", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"([^'′])(\d+)\s+(\d+)\s*[\"″]", r"\1\2' \3\"", cleaned)
        
        # Fix 3: Normalize spacing around × symbol
        cleaned = re.sub(r"\s*([xX×])\s*", r" \1 ", cleaned)
        
        # Fix 4: Remove malformed dimensions like "13' 2 10 10\"" (too many numbers)
        # We'll just let the regex not match these
        
        return cleaned
    
    def _parse_dimension_groups(
        self,
        groups: Tuple,
        pattern: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse regex groups into dimension values.
        
        Args:
            groups: Regex match groups
            pattern: Pattern used for matching
        
        Returns:
            Parsed dimension data or None
        """
        try:
            # Pattern 1: Feet and inches (e.g., 13'2" x 9'1")
            # This pattern has 4 groups: feet1, inches1, feet2, inches2
            if "['′]" in pattern and len(groups) >= 4:
                feet1 = int(groups[0])
                inches1 = int(groups[1]) if groups[1] else 0
                feet2 = int(groups[2])
                inches2 = int(groups[3]) if groups[3] else 0
                
                length = feet1 + (inches1 / 12.0)
                width = feet2 + (inches2 / 12.0)
                
                return {
                    'length': round(length, 2),
                    'width': round(width, 2),
                    'format': 'feet_inches'
                }
            
            # Pattern 2: Decimal (e.g., 13.2 x 9.1) or Feet-only (e.g., 13 x 9)
            # This pattern has 2 groups: val1, val2
            elif len(groups) == 2:
                val1 = float(groups[0])
                val2 = float(groups[1])
                
                # Determine if it's decimal or feet-only based on the pattern
                if r'\.' in pattern: # If the pattern explicitly looks for a decimal point
                    return {
                        'length': round(val1, 2),
                        'width': round(val2, 2),
                        'format': 'decimal'
                    }
                else: # Assume feet-only if no decimal in pattern, but numbers are floats
                    return {
                        'length': round(val1, 2),
                        'width': round(val2, 2),
                        'format': 'feet_only'
                    }
            
            # Pattern 3: Hyphen format (e.g., 13-2 x 9-1)
            # This pattern has 4 groups: feet1, inches1, feet2, inches2
            elif len(groups) == 4:
                feet1 = int(groups[0])
                inches1 = int(groups[1])
                feet2 = int(groups[2])
                inches2 = int(groups[3])
                
                length = feet1 + (inches1 / 12.0)
                width = feet2 + (inches2 / 12.0)
                
                return {
                    'length': round(length, 2),
                    'width': round(width, 2),
                    'format': 'feet_inches_hyphen'
                }
        
        except (ValueError, TypeError) as e:
            print(f"Dimension parsing error: {e}")
            return None
        
        return None
    
    def extract_room_labels(
        self,
        text_boxes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract potential room labels from OCR text boxes.
        
        Args:
            text_boxes: List of text boxes from OCR
        
        Returns:
            List of potential room labels
        """
        # Common room keywords
        room_keywords = [
            'bedroom', 'bed room', 'master', 'guest',
            'living', 'dining', 'kitchen', 'bathroom', 'bath',
            'garage', 'hall', 'entry', 'foyer', 'office',
            'closet', 'laundry', 'utility', 'storage',
            'balcony', 'porch', 'deck', 'patio'
        ]
        
        room_labels = []
        
        for box in text_boxes:
            text_lower = box['text'].lower()
            
            # Check if text contains room keywords
            for keyword in room_keywords:
                if keyword in text_lower:
                    room_labels.append({
                        'label': box['text'],
                        'keyword': keyword,
                        'confidence': box['confidence'],
                        'bbox': box['bbox']
                    })
                    break
        
        return room_labels
    
    def process_floorplan_image(
        self,
        image: np.ndarray
    ) -> Dict[str, Any]:
        """
        Complete OCR processing pipeline for floor plan.
        Automatically handles images of ANY size!
        
        Args:
            image: Floor plan image (any size)
        
        Returns:
            Comprehensive OCR results
        """
        print("\n" + "#"*80)
        print("🏗️  FLOOR PLAN OCR PROCESSING STARTED")
        print("#"*80)
        
        # Step 0: Resize if too large (prevents memory issues)
        print(f"\n📐 Input image: {image.shape[1]}x{image.shape[0]} pixels")
        image = self.resize_if_needed(image, max_width=2000)
        
        # Step 1: Extract text - Priority order: Gemini → Azure OpenAI → Google Vision → EasyOCR → Tesseract
        if self.gemini:
            # Use Gemini 1.5 Pro (PRIMARY for testing)
            print("\n🤖 [GEMINI] Using Gemini 1.5 Pro for intelligent extraction...")
            ocr_result = self.gemini.extract_dimensions(image)
            
            # If Gemini returns low confidence, try GPT-4 as fallback
            if ocr_result.get('total_dimensions_found', 0) == 0 and self.azure_openai:
                print("⚠️  Gemini found no dimensions, trying GPT-4 fallback...")
                ocr_result = self.azure_openai.extract_dimensions(image)
            
            return ocr_result
        
        elif self.azure_openai:
            # Use Azure OpenAI GPT-4 Vision (FALLBACK 1 - AI-powered intelligent extraction)
            print("\n🤖 [AZURE OPENAI] Using GPT-4 Vision for intelligent extraction...")
            ocr_result = self.azure_openai.extract_dimensions(image)
            return ocr_result
        
        elif self.google_vision:
            # Use Google Vision (FALLBACK 1 - good OCR, needs regex parsing)
            print("\n🌐 [GOOGLE VISION] Using Google Vision API for OCR...")
            ocr_result = self.google_vision.extract_text(image)
        elif self.easyocr_reader:
            # Use EasyOCR (FALLBACK 2 - decent for clean floor plans)
            print("\n👁️  [EASYOCR] Using EasyOCR...")
            ocr_result = self.extract_text_easyocr(image, preprocess=True)
        else:
            # Use Tesseract (LAST RESORT - struggles with blueprints)
            print("\n📖 [TESSERACT] Using Tesseract OCR...")
            ocr_result = self.extract_text(image, preprocess=True)
        
        print(f"\n📊 OCR Extraction Results:")
        print(f"  • Text regions found: {len(ocr_result['text_boxes'])}")
        print(f"  • Total text length: {len(ocr_result['text'])} characters")
        print(f"\n🔤 Sample of text boxes (first 10):")
        for i, box in enumerate(ocr_result['text_boxes'][:10]):
            print(f"  {i+1}. '{box['text']}' (confidence: {box['confidence']:.1f}%)")
        
        # Find dimensions
        dimensions = self.find_dimensions(ocr_result['text'])
        
        # Extract room labels
        print("\n" + "="*80)
        print("🏷️  DEBUG: ROOM LABEL EXTRACTION")
        print("="*80)
        room_labels = self.extract_room_labels(ocr_result['text_boxes'])
        print(f"📊 TOTAL ROOM LABELS FOUND: {len(room_labels)}")
        for i, label in enumerate(room_labels):
            print(f"  {i+1}. '{label['label']}' (keyword: {label['keyword']}, confidence: {label['confidence']:.1f}%)")
        print("="*80 + "\n")
        
        print("\n" + "#"*80)
        print("✅ FLOOR PLAN OCR PROCESSING COMPLETE")
        print(f"   Dimensions: {len(dimensions)} | Room Labels: {len(room_labels)} | Text Regions: {len(ocr_result['text_boxes'])}")
        print("#"*80 + "\n")
        
        return {
            'full_text': ocr_result['text'],
            'text_boxes': ocr_result['text_boxes'],
            'dimensions': dimensions,
            'room_labels': room_labels,
            'total_dimensions_found': len(dimensions),
            'total_rooms_found': len(room_labels)
        }
