"""Floor plan analysis service for room detection and dimension extraction."""
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from services.floorplan_ocr import FloorPlanOCR
from services.calculation_engine import CalculationEngine


class FloorPlanAnalyzer:
    """Service for analyzing architectural floor plans."""
    
    # Standard dimensions (in feet)
    DEFAULT_CEILING_HEIGHT = 10.0
    DEFAULT_DOOR_HEIGHT = 7.0
    DEFAULT_DOOR_WIDTH = 3.0
    DEFAULT_WINDOW_HEIGHT = 4.0
    DEFAULT_WINDOW_WIDTH = 3.0
    
    def __init__(self, ocr_service: Optional[FloorPlanOCR] = None):
        """
        Initialize floor plan analyzer.
        
        Args:
            ocr_service: OCR service instance (creates new if None)
        """
        self.ocr = ocr_service or FloorPlanOCR()
        self.calc_engine = CalculationEngine()
    
    def detect_rooms(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect room boundaries using contour detection.
        
        Args:
            image: Floor plan image
        
        Returns:
            List of detected room regions
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(
            cleaned,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter and sort contours by area
        height, width = image.shape[:2]
        min_area = (width * height) * 0.01  # Minimum 1% of image
        max_area = (width * height) * 0.3   # Maximum 30% of image
        
        rooms = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            if min_area < area < max_area:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate center point
                center_x = x + w // 2
                center_y = y + h // 2
                
                rooms.append({
                    'id': i,
                    'contour': contour,
                    'bbox': {'x': x, 'y': y, 'w': w, 'h': h},
                    'center': {'x': center_x, 'y': center_y},
                    'area': area
                })
        
        # Sort by area (largest first)
        rooms.sort(key=lambda r: r['area'], reverse=True)
        
        return rooms
    
    def match_dimensions_to_rooms(
        self,
        rooms: List[Dict[str, Any]],
        dimensions: List[Dict[str, Any]],
        text_boxes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match extracted dimensions to detected room regions.
        
        Args:
            rooms: Detected room regions
            dimensions: Extracted dimension data
            text_boxes: OCR text boxes
        
        Returns:
            Rooms with matched dimensions
        """
        # Create spatial index for text boxes
        text_spatial = {}
        for box in text_boxes:
            center_x = box['bbox']['x'] + box['bbox']['w'] // 2
            center_y = box['bbox']['y'] + box['bbox']['h'] // 2
            text_spatial[box['text']] = (center_x, center_y)
        
        # Match dimensions to rooms based on proximity
        for room in rooms:
            room_center = (room['center']['x'], room['center']['y'])
            closest_dim = None
            min_distance = float('inf')
            
            # Find dimension text closest to room center
            for dim in dimensions:
                # Try to find the position of this dimension text
                dim_text = dim['raw_text']
                
                # Search for this text in text boxes
                for text, pos in text_spatial.items():
                    if dim_text in text or text in dim_text:
                        distance = np.sqrt(
                            (pos[0] - room_center[0])**2 + 
                            (pos[1] - room_center[1])**2
                        )
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_dim = dim
                            break
            
            if closest_dim:
                room['dimensions'] = {
                    'length': closest_dim['length'],
                    'width': closest_dim['width'],
                    'raw_text': closest_dim['raw_text']
                }
            else:
                room['dimensions'] = None
        
        return rooms
    
    def match_labels_to_rooms(
        self,
        rooms: List[Dict[str, Any]],
        room_labels: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match room labels to detected room regions.
        
        Args:
            rooms: Detected room regions
            room_labels: Extracted room labels
        
        Returns:
            Rooms with matched labels
        """
        for room in rooms:
            room_center = (room['center']['x'], room['center']['y'])
            closest_label = None
            min_distance = float('inf')
            
            # Find label closest to room center
            for label in room_labels:
                label_x = label['bbox']['x'] + label['bbox']['w'] // 2
                label_y = label['bbox']['y'] + label['bbox']['h'] // 2
                
                distance = np.sqrt(
                    (label_x - room_center[0])**2 + 
                    (label_y - room_center[1])**2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_label = label
            
            if closest_label and min_distance < room['bbox']['w']:
                room['name'] = closest_label['label']
                room['name_confidence'] = closest_label['confidence']
            else:
                room['name'] = f"Room {room['id'] + 1}"
                room['name_confidence'] = 0.0
        
        return rooms
    
    def calculate_wall_area(
        self,
        length: float,
        width: float,
        ceiling_height: float = DEFAULT_CEILING_HEIGHT,
        num_doors: int = 1,
        num_windows: int = 1
    ) -> Dict[str, float]:
        """
        Calculate wall area from floor dimensions.
        
        Args:
            length: Room length in feet
            width: Room width in feet
            ceiling_height: Ceiling height in feet
            num_doors: Number of doors
            num_windows: Number of windows
        
        Returns:
            Dictionary with area calculations
        """
        # Calculate perimeter
        perimeter = 2 * (length + width)
        
        # Calculate total wall area
        total_wall_area = perimeter * ceiling_height
        
        # Calculate door area
        door_area = num_doors * self.DEFAULT_DOOR_HEIGHT * self.DEFAULT_DOOR_WIDTH
        
        # Calculate window area
        window_area = num_windows * self.DEFAULT_WINDOW_HEIGHT * self.DEFAULT_WINDOW_WIDTH
        
        # Calculate paintable area (wall area - doors - windows)
        paintable_area = total_wall_area - door_area - window_area
        
        return {
            'floor_area': length * width,
            'perimeter': perimeter,
            'total_wall_area': total_wall_area,
            'door_area': door_area,
            'window_area': window_area,
            'paintable_area': max(paintable_area, 0)  # Ensure non-negative
        }
    
    def estimate_door_window_counts(self, room_name: str) -> Tuple[int, int]:
        """
        Estimate number of doors and windows based on room type.
        
        Args:
            room_name: Name/type of the room
        
        Returns:
            Tuple of (num_doors, num_windows)
        """
        room_name_lower = room_name.lower()
        
        # Garage - usually has 1-2 doors, 0-1 windows
        if 'garage' in room_name_lower:
            return (1, 0)
        
        # Bathroom - usually 1 door, 1 window
        elif 'bath' in room_name_lower:
            return (1, 1)
        
        # Kitchen - usually 1 door, 1-2 windows
        elif 'kitchen' in room_name_lower:
            return (1, 2)
        
        # Bedroom - usually 1 door, 1-2 windows
        elif 'bed' in room_name_lower or 'master' in room_name_lower:
            return (1, 2)
        
        # Living/Dining - usually 1 door, 2-3 windows
        elif 'living' in room_name_lower or 'dining' in room_name_lower:
            return (1, 3)
        
        # Hall/Entry - usually 1-2 doors, 0-1 windows
        elif 'hall' in room_name_lower or 'entry' in room_name_lower or 'foyer' in room_name_lower:
            return (2, 0)
        
        # Default - 1 door, 1 window
        else:
            return (1, 1)
    
    def process_floorplan(
        self,
        image: np.ndarray,
        ceiling_height: float = DEFAULT_CEILING_HEIGHT,
        paint_type: str = "interior",
        num_coats: int = 2,
        include_ceiling: bool = False
    ) -> Dict[str, Any]:
        """
        Complete floor plan processing pipeline.
        
        Args:
            image: Floor plan image
            ceiling_height: Ceiling height in feet
            paint_type: Type of paint (interior/exterior)
            num_coats: Number of coats
            include_ceiling: Whether to include ceiling painting
        
        Returns:
            Complete floor plan analysis results
        """
        # Step 1: OCR extraction
        print("\n" + "="*80)
        print("🗺️  STEP 1: OCR EXTRACTION")
        print("="*80)
        ocr_result = self.ocr.process_floorplan_image(image)
        
        # Step 2: Detect rooms
        print("\n" + "="*80)
        print("🔳 STEP 2: ROOM BOUNDARY DETECTION")
        print("="*80)
        rooms = self.detect_rooms(image)
        print(f"📊 Detected {len(rooms)} room boundaries via contour detection")
        
        # Fallback: If no rooms detected via contours, create virtual rooms from dimensions
        if len(rooms) == 0 and len(ocr_result['dimensions']) > 0:
            print(f"\n⚠️  No room boundaries detected, creating virtual rooms from {len(ocr_result['dimensions'])} dimensions")
            rooms = []
            
            # Try to match dimensions with room labels
            room_labels = ocr_result['room_labels']
            
            for i, dim in enumerate(ocr_result['dimensions']):
                # Try to find a matching label
                room_name = f'Room {i + 1}'
                if i < len(room_labels):
                    room_name = room_labels[i]['label']
                
                print(f"  {i+1}. Creating virtual room: '{room_name}' with dimensions {dim['length']}ft × {dim['width']}ft")
                
                rooms.append({
                    'id': i,
                    'bbox': {'x': 0, 'y': 0, 'w': 100, 'h': 100},  # Dummy bbox
                    'center': {'x': 50, 'y': 50},  # Dummy center
                    'area': 10000,  # Dummy area
                    'dimensions': dim,  # Directly assign dimension
                    'name': room_name,  # Use matched label or default
                    'name_confidence': room_labels[i]['confidence'] if i < len(room_labels) else 0.0
                })
            
            print(f"✅ Created {len(rooms)} virtual rooms with dimensions")
        else:
            # Step 3: Match dimensions to rooms (only if rooms were detected)
            print("\n" + "="*80)
            print("🔗 STEP 3: MATCHING DIMENSIONS TO ROOMS")
            print("="*80)
            rooms = self.match_dimensions_to_rooms(
                rooms,
                ocr_result['dimensions'],
                ocr_result['text_boxes']
            )
            
            # Step 4: Match labels to rooms
            print("\n" + "="*80)
            print("🏷️  STEP 4: MATCHING LABELS TO ROOMS")
            print("="*80)
            rooms = self.match_labels_to_rooms(rooms, ocr_result['room_labels'])
        
        # Step 5: Calculate paint for each room
        room_results = []
        total_area = 0
        total_paintable_area = 0
        total_paint_required = 0
        total_cost = 0
        
        for room in rooms:
            # Skip rooms without dimensions
            if not room.get('dimensions'):
                continue
            
            length = room['dimensions']['length']
            width = room['dimensions']['width']
            
            # Estimate doors and windows
            num_doors, num_windows = self.estimate_door_window_counts(room['name'])
            
            # Use the calculation engine's complete estimation method
            estimation = self.calc_engine.calculate_room_estimation(
                length=length,
                width=width,
                height=ceiling_height,
                num_doors=num_doors,
                num_windows=num_windows,
                paint_type=paint_type,
                num_coats=num_coats,
                include_ceiling=include_ceiling,
                include_primer=True,
                include_putty=True
            )
            
            room_result = {
                'name': room['name'],
                'dimensions': {
                    'length': length,
                    'width': width,
                    'height': ceiling_height
                },
                'num_doors': num_doors,
                'num_windows': num_windows,
                'areas': {
                    'floor_area': length * width,
                    'wall_area': estimation.area_calculation.total_wall_area,
                    'paintable_area': estimation.area_calculation.paintable_area
                },
                'paint': {
                    'liters': estimation.product_breakdown.paint.quantity,
                    'cost': estimation.product_breakdown.paint.total_cost
                },
                'primer': {
                    'liters': estimation.product_breakdown.primer.quantity if estimation.product_breakdown.primer else 0,
                    'cost': estimation.product_breakdown.primer.total_cost if estimation.product_breakdown.primer else 0
                } if estimation.product_breakdown.primer else None,
                'putty': {
                    'kg': estimation.product_breakdown.putty.quantity if estimation.product_breakdown.putty else 0,
                    'cost': estimation.product_breakdown.putty.total_cost if estimation.product_breakdown.putty else 0
                } if estimation.product_breakdown.putty else None,
                'total_cost': estimation.cost_breakdown.total_cost,
                'confidence': room.get('name_confidence', 0.0)
            }
            
            room_results.append(room_result)
            
            # Aggregate totals
            total_area += length * width
            total_paintable_area += estimation.area_calculation.paintable_area
            total_paint_required += estimation.product_breakdown.paint.quantity
            total_cost += estimation.cost_breakdown.total_cost
        
        return {
            'success': True,
            'rooms': room_results,
            'total_rooms': len(room_results),
            'total_floor_area': round(total_area, 2),
            'total_paintable_area': round(total_paintable_area, 2),
            'total_paint_required_liters': round(total_paint_required, 2),
            'total_cost': round(total_cost, 2),
            'ocr_metadata': {
                'dimensions_found': ocr_result['total_dimensions_found'],
                'room_labels_found': ocr_result['total_rooms_found'],
                'text_regions': len(ocr_result['text_boxes'])
            }
        }
