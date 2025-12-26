"""Calculation engine for paint estimation."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from utils.math_utils import (
    calculate_wall_area,
    calculate_ceiling_area,
    calculate_paint_quantity,
    calculate_putty_quantity,
    calculate_cost
)
from schemas.output_models import (
    AreaCalculation,
    ProductQuantity,
    ProductBreakdown,
    CostBreakdown,
    EstimationOutput
)

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CalculationEngine:
    """Engine for paint estimation calculations."""
    
    def __init__(self, config_path: str = "utils/paint_config.json", debug_mode: bool = False):
        """
        Initialize calculation engine.
        
        Args:
            config_path: Path to paint configuration JSON
            debug_mode: Enable detailed debug logging
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.debug_mode = debug_mode
        
        if debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("Calculation engine initialized in DEBUG mode")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load paint configuration from JSON."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Paint configuration not found at {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in paint configuration: {self.config_path}")
    
    def get_paint_product(self, paint_type: str, product_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get paint product details.
        
        Args:
            paint_type: 'interior' or 'exterior'
            product_key: Specific product key (optional)
        
        Returns:
            Product configuration dictionary
        """
        paint_type = paint_type.lower()
        products = self.config['paint_products'].get(paint_type, {})
        
        if not products:
            raise ValueError(f"No products found for paint type: {paint_type}")
        
        if product_key:
            product = products.get(product_key)
            if not product:
                raise ValueError(f"Product '{product_key}' not found for {paint_type} paint")
            return product
        
        # Return the first product as default
        default_key = list(products.keys())[0]
        return products[default_key]
    
    def get_primer(self, paint_type: str) -> Dict[str, Any]:
        """Get primer details based on paint type."""
        primer_key = f"{paint_type}_primer"
        primer = self.config['primers'].get(primer_key)
        
        if not primer:
            # Fallback to first available primer
            primer_key = list(self.config['primers'].keys())[0]
            primer = self.config['primers'][primer_key]
        
        return primer
    
    def get_putty(self) -> Dict[str, Any]:
        """Get wall putty details."""
        return self.config['putty']['wall_putty']
    
    def calculate_room_estimation(
        self,
        length: float,
        width: float,
        height: float,
        num_doors: int = 0,
        num_windows: int = 0,
        door_height: float = 7.0,
        door_width: float = 3.0,
        window_height: float = 4.0,
        window_width: float = 3.0,
        paint_type: str = "interior",
        paint_product: Optional[str] = None,
        num_coats: int = 2,
        include_ceiling: bool = False,
        include_primer: bool = True,
        include_putty: bool = True
    ) -> EstimationOutput:
        """
        Calculate complete paint estimation for a room.
        
        Args:
            length: Room length in feet
            width: Room width in feet
            height: Room height in feet
            num_doors: Number of doors
            num_windows: Number of windows
            door_height: Door height in feet
            door_width: Door width in feet
            window_height: Window height in feet
            window_width: Window width in feet
            paint_type: 'interior' or 'exterior'
            paint_product: Specific product key
            num_coats: Number of coats
            include_ceiling: Paint ceiling or not
            include_primer: Include primer in estimation
            include_putty: Include putty in estimation
        
        Returns:
            Complete estimation output
        """
        if self.debug_mode:
            logger.debug(f"Starting calculation with params: L={length}, W={width}, H={height}, "
                        f"doors={num_doors}, windows={num_windows}, coats={num_coats}")
        
        # Calculate areas
        total_wall_area, door_area, window_area, paintable_area = calculate_wall_area(
            length=length,
            width=width,
            height=height,
            num_doors=num_doors,
            num_windows=num_windows,
            door_height=door_height,
            door_width=door_width,
            window_height=window_height,
            window_width=window_width
        )
        
        if self.debug_mode:
            logger.debug(f"Area calculation: total_wall={total_wall_area}, "
                        f"doors={door_area}, windows={window_area}, paintable={paintable_area}")
        
        ceiling_area_value = None
        if include_ceiling:
            ceiling_area_value = calculate_ceiling_area(length, width)
            paintable_area += ceiling_area_value
        
        # Get product details
        paint_product_info = self.get_paint_product(paint_type, paint_product)
        wastage_factor = self.config['calculation_factors']['wastage_factor']
        
        # Calculate paint quantity
        paint_quantity = calculate_paint_quantity(
            paintable_area=paintable_area,
            coverage_per_liter=paint_product_info['coverage_per_liter'],
            num_coats=num_coats,
            wastage_factor=wastage_factor
        )
        paint_cost = calculate_cost(paint_quantity, paint_product_info['price_per_liter'])
        
        if self.debug_mode:
            logger.debug(f"Paint: {paint_quantity:.2f}L × ₹{paint_product_info['price_per_liter']:.2f} = ₹{paint_cost:.2f}")
        
        # Create paint product quantity
        paint_prod_qty = ProductQuantity(
            product_name=paint_product_info['name'],
            product_type="paint",
            quantity=paint_quantity,
            unit="liters",
            price_per_unit=paint_product_info['price_per_liter'],
            total_cost=paint_cost,
            coverage_per_unit=paint_product_info['coverage_per_liter']
        )
        
        # Calculate primer if needed
        primer_prod_qty = None
        primer_cost = 0.0
        if include_primer:
            primer_info = self.get_primer(paint_type)
            primer_quantity = calculate_paint_quantity(
                paintable_area=paintable_area,
                coverage_per_liter=primer_info['coverage_per_liter'],
                num_coats=1,  # Usually 1 coat of primer
                wastage_factor=wastage_factor
            )
            primer_cost = calculate_cost(primer_quantity, primer_info['price_per_liter'])
            
            primer_prod_qty = ProductQuantity(
                product_name=primer_info['name'],
                product_type="primer",
                quantity=primer_quantity,
                unit="liters",
                price_per_unit=primer_info['price_per_liter'],
                total_cost=primer_cost,
                coverage_per_unit=primer_info['coverage_per_liter']
            )
        
        # Calculate putty if needed
        putty_prod_qty = None
        putty_cost = 0.0
        if include_putty:
            putty_info = self.get_putty()
            putty_quantity = calculate_putty_quantity(
                paintable_area=paintable_area,
                coverage_per_kg=putty_info['coverage_per_kg'],
                num_coats=putty_info['coats_recommended'],
                wastage_factor=wastage_factor
            )
            putty_cost = calculate_cost(putty_quantity, putty_info['price_per_kg'])
            
            if self.debug_mode:
                logger.debug(f"Putty: {putty_quantity:.2f}kg × ₹{putty_info['price_per_kg']:.2f} = ₹{putty_cost:.2f}")
            
            putty_prod_qty = ProductQuantity(
                product_name=putty_info['name'],
                product_type="putty",
                quantity=putty_quantity,
                unit="kg",
                price_per_unit=putty_info['price_per_kg'],
                total_cost=putty_cost,
                coverage_per_unit=putty_info['coverage_per_kg']
            )
        
        # Create area calculation
        area_calc = AreaCalculation(
            total_wall_area=round(total_wall_area, 2),
            door_area=round(door_area, 2),
            window_area=round(window_area, 2),
            ceiling_area=round(ceiling_area_value, 2) if ceiling_area_value else None,
            paintable_area=round(paintable_area, 2)
        )
        
        # Create product breakdown
        product_breakdown = ProductBreakdown(
            primer=primer_prod_qty,
            putty=putty_prod_qty,
            paint=paint_prod_qty
        )
        
        # Create cost breakdown
        total_cost = primer_cost + putty_cost + paint_cost
        cost_breakdown = CostBreakdown(
            primer_cost=round(primer_cost, 2),
            putty_cost=round(putty_cost, 2),
            paint_cost=round(paint_cost, 2),
            total_cost=round(total_cost, 2)
        )
        
        if self.debug_mode:
            logger.debug(f"Cost breakdown: primer=₹{primer_cost:.2f}, putty=₹{putty_cost:.2f}, "
                        f"paint=₹{paint_cost:.2f}, TOTAL=₹{total_cost:.2f}")
        
        # Create summary
        summary = {
            "paintable_area_sqft": round(paintable_area, 2),
            "paint_required_liters": paint_quantity,
            "total_cost_inr": round(total_cost, 2),
            "estimated_cost_range": f"₹{round(total_cost * 0.9, 2)} - ₹{round(total_cost * 1.1, 2)}",
            "num_coats": num_coats,
            "paint_type": paint_type,
            "paint_name": paint_product_info['name']
        }
        
        # Create final output
        return EstimationOutput(
            area_calculation=area_calc,
            product_breakdown=product_breakdown,
            cost_breakdown=cost_breakdown,
            paint_type=paint_type,
            num_coats=num_coats,
            summary=summary
        )
