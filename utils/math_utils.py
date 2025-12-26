"""Math utilities for paint estimation calculations."""
from typing import Tuple


def calculate_wall_area(
    length: float,
    width: float,
    height: float,
    num_doors: int = 0,
    num_windows: int = 0,
    door_height: float = 7.0,
    door_width: float = 3.0,
    window_height: float = 4.0,
    window_width: float = 3.0
) -> Tuple[float, float, float, float]:
    """
    Calculate the paintable wall area of a room.
    
    Args:
        length: Room length in feet
        width: Room width in feet
        height: Room height/ceiling height in feet
        num_doors: Number of doors
        num_windows: Number of windows
        door_height: Height of each door in feet
        door_width: Width of each door in feet
        window_height: Height of each window in feet
        window_width: Width of each window in feet
    
    Returns:
        Tuple of (total_wall_area, door_area, window_area, paintable_area)
    """
    # Calculate total wall area (4 walls)
    wall_area_1 = 2 * length * height  # Two longer walls
    wall_area_2 = 2 * width * height   # Two shorter walls
    total_wall_area = wall_area_1 + wall_area_2
    
    # Calculate door and window areas
    door_area = num_doors * door_height * door_width
    window_area = num_windows * window_height * window_width
    
    # Calculate paintable area (subtract doors and windows)
    paintable_area = total_wall_area - door_area - window_area
    
    # Ensure paintable area is not negative
    paintable_area = max(0, paintable_area)
    
    return total_wall_area, door_area, window_area, paintable_area


def calculate_ceiling_area(length: float, width: float) -> float:
    """
    Calculate ceiling area.
    
    Args:
        length: Room length in feet
        width: Room width in feet
    
    Returns:
        Ceiling area in square feet
    """
    return length * width


def calculate_paint_quantity(
    paintable_area: float,
    coverage_per_liter: float,
    num_coats: int = 2,
    wastage_factor: float = 1.1
) -> float:
    """
    Calculate paint quantity required in liters.
    
    Args:
        paintable_area: Area to be painted in sq ft
        coverage_per_liter: Coverage per liter in sq ft/liter
        num_coats: Number of coats to apply
        wastage_factor: Wastage multiplier (default 1.1 for 10% wastage)
    
    Returns:
        Paint quantity in liters
    """
    if coverage_per_liter <= 0:
        raise ValueError("Coverage per liter must be positive")
    
    raw_quantity = (paintable_area * num_coats) / coverage_per_liter
    quantity_with_wastage = raw_quantity * wastage_factor
    
    return round(quantity_with_wastage, 2)


def calculate_putty_quantity(
    paintable_area: float,
    coverage_per_kg: float = 20.0,
    num_coats: int = 2,
    wastage_factor: float = 1.1
) -> float:
    """
    Calculate putty quantity required in kg.
    
    Args:
        paintable_area: Area to be painted in sq ft
        coverage_per_kg: Coverage per kg in sq ft/kg
        num_coats: Number of coats to apply
        wastage_factor: Wastage multiplier
    
    Returns:
        Putty quantity in kg
    """
    if coverage_per_kg <= 0:
        raise ValueError("Coverage per kg must be positive")
    
    raw_quantity = (paintable_area * num_coats) / coverage_per_kg
    quantity_with_wastage = raw_quantity * wastage_factor
    
    return round(quantity_with_wastage, 2)


def calculate_cost(
    quantity: float,
    price_per_unit: float
) -> float:
    """
    Calculate total cost.
    
    Args:
        quantity: Quantity in liters or kg
        price_per_unit: Price per unit in rupees
    
    Returns:
        Total cost in rupees
    """
    return round(quantity * price_per_unit, 2)


def sqft_to_sqm(area_sqft: float) -> float:
    """Convert square feet to square meters."""
    return round(area_sqft * 0.092903, 2)


def sqm_to_sqft(area_sqm: float) -> float:
    """Convert square meters to square feet."""
    return round(area_sqm * 10.7639, 2)


def meters_to_feet(meters: float) -> float:
    """Convert meters to feet."""
    return round(meters * 3.28084, 2)


def feet_to_meters(feet: float) -> float:
    """Convert feet to meters."""
    return round(feet * 0.3048, 2)
