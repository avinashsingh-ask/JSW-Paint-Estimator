"""Debug utilities for calculation verification and troubleshooting."""
from typing import Dict, Any, List
import json
from datetime import datetime


class CalculationDebugger:
    """Utility class for debugging and verifying calculations."""
    
    def __init__(self):
        self.debug_log: List[Dict[str, Any]] = []
    
    def log_step(self, step_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any], formula: str = ""):
        """
        Log a calculation step.
        
        Args:
            step_name: Name of the calculation step
            inputs: Input parameters
            outputs: Output values
            formula: Formula used (optional)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "inputs": inputs,
            "outputs": outputs,
            "formula": formula
        }
        self.debug_log.append(log_entry)
    
    def verify_calculation(
        self,
        expected: float,
        actual: float,
        tolerance: float = 0.01,
        description: str = ""
    ) -> bool:
        """
        Verify a calculation result.
        
        Args:
            expected: Expected value
            actual: Actual calculated value
            tolerance: Acceptable difference
            description: Description of what's being verified
        
        Returns:
            True if within tolerance, False otherwise
        """
        difference = abs(expected - actual)
        is_correct = difference <= tolerance
        
        log_entry = {
            "verification": description,
            "expected": expected,
            "actual": actual,
            "difference": difference,
            "tolerance": tolerance,
            "passed": is_correct
        }
        self.debug_log.append(log_entry)
        
        return is_correct
    
    def generate_report(self) -> str:
        """Generate a detailed debug report."""
        report = ["=" * 80]
        report.append("CALCULATION DEBUG REPORT")
        report.append("=" * 80)
        report.append("")
        
        for entry in self.debug_log:
            if "step" in entry:
                report.append(f"\n📊 STEP: {entry['step']}")
                report.append(f"   Timestamp: {entry['timestamp']}")
                
                if entry.get('formula'):
                    report.append(f"   Formula: {entry['formula']}")
                
                report.append("   Inputs:")
                for key, value in entry['inputs'].items():
                    report.append(f"      {key}: {value}")
                
                report.append("   Outputs:")
                for key, value in entry['outputs'].items():
                    report.append(f"      {key}: {value}")
            
            elif "verification" in entry:
                status = "✅ PASS" if entry['passed'] else "❌ FAIL"
                report.append(f"\n{status}: {entry['verification']}")
                report.append(f"   Expected: {entry['expected']}")
                report.append(f"   Actual: {entry['actual']}")
                report.append(f"   Difference: {entry['difference']}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
    
    def export_json(self) -> str:
        """Export debug log as JSON."""
        return json.dumps(self.debug_log, indent=2)
    
    def clear(self):
        """Clear the debug log."""
        self.debug_log = []


def format_calculation_breakdown(data: Dict[str, Any]) -> str:
    """
    Format a calculation breakdown for display.
    
    Args:
        data: Estimation output data
    
    Returns:
        Formatted string representation
    """
    lines = []
    
    lines.append("=" * 60)
    lines.append("PAINT ESTIMATION BREAKDOWN")
    lines.append("=" * 60)
    
    # Area calculations
    lines.append("\n📐 AREA CALCULATIONS")
    lines.append("-" * 60)
    area = data.get('area_calculation', {})
    lines.append(f"Total Wall Area:    {area.get('total_wall_area', 0):>10.2f} sq ft")
    lines.append(f"Door Area:          {area.get('door_area', 0):>10.2f} sq ft")
    lines.append(f"Window Area:        {area.get('window_area', 0):>10.2f} sq ft")
    if area.get('ceiling_area'):
        lines.append(f"Ceiling Area:       {area.get('ceiling_area', 0):>10.2f} sq ft")
    lines.append(f"{'Paintable Area:':20}{area.get('paintable_area', 0):>10.2f} sq ft")
    
    # Product breakdown
    lines.append("\n🎨 PRODUCT REQUIREMENTS")
    lines.append("-" * 60)
    products = data.get('product_breakdown', {})
    
    if products.get('primer'):
        primer = products['primer']
        lines.append(f"\nPrimer: {primer['product_name']}")
        lines.append(f"  Quantity:  {primer['quantity']:>8.2f} {primer['unit']}")
        lines.append(f"  Price:     ₹{primer['price_per_unit']:>8.2f}/{primer['unit']}")
        lines.append(f"  Cost:      ₹{primer['total_cost']:>8.2f}")
    
    if products.get('putty'):
        putty = products['putty']
        lines.append(f"\nPutty: {putty['product_name']}")
        lines.append(f"  Quantity:  {putty['quantity']:>8.2f} {putty['unit']}")
        lines.append(f"  Price:     ₹{putty['price_per_unit']:>8.2f}/{putty['unit']}")
        lines.append(f"  Cost:      ₹{putty['total_cost']:>8.2f}")
    
    if products.get('paint'):
        paint = products['paint']
        lines.append(f"\nPaint: {paint['product_name']}")
        lines.append(f"  Quantity:  {paint['quantity']:>8.2f} {paint['unit']}")
        lines.append(f"  Price:     ₹{paint['price_per_unit']:>8.2f}/{paint['unit']}")
        lines.append(f"  Cost:      ₹{paint['total_cost']:>8.2f}")
    
    # Cost breakdown
    lines.append("\n💰 COST BREAKDOWN")
    lines.append("-" * 60)
    costs = data.get('cost_breakdown', {})
    if costs.get('primer_cost', 0) > 0:
        lines.append(f"Primer Cost:        ₹{costs.get('primer_cost', 0):>10.2f}")
    if costs.get('putty_cost', 0) > 0:
        lines.append(f"Putty Cost:         ₹{costs.get('putty_cost', 0):>10.2f}")
    lines.append(f"Paint Cost:         ₹{costs.get('paint_cost', 0):>10.2f}")
    lines.append("-" * 60)
    lines.append(f"{'TOTAL COST:':20}₹{costs.get('total_cost', 0):>10.2f}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def verify_estimation_calculation(
    length: float,
    width: float,
    height: float,
    num_doors: int,
    num_windows: int,
    door_height: float,
    door_width: float,
    window_height: float,
    window_width: float,
    num_coats: int,
    paint_coverage: float,
    paint_price: float,
    putty_coverage: float,
    putty_price: float,
    wastage_factor: float = 1.1
) -> Dict[str, Any]:
    """
    Manually verify calculation with step-by-step breakdown.
    
    Returns:
        Dictionary with expected values at each step
    """
    debugger = CalculationDebugger()
    
    # Step 1: Calculate wall area
    wall_area_1 = 2 * length * height
    wall_area_2 = 2 * width * height
    total_wall_area = wall_area_1 + wall_area_2
    
    debugger.log_step(
        "Calculate Total Wall Area",
        {"length": length, "width": width, "height": height},
        {"wall_area_1": wall_area_1, "wall_area_2": wall_area_2, "total": total_wall_area},
        "2 × (length × height) + 2 × (width × height)"
    )
    
    # Step 2: Calculate openings
    door_area = num_doors * door_height * door_width
    window_area = num_windows * window_height * window_width
    
    debugger.log_step(
        "Calculate Door and Window Areas",
        {
            "num_doors": num_doors, "door_h": door_height, "door_w": door_width,
            "num_windows": num_windows, "window_h": window_height, "window_w": window_width
        },
        {"door_area": door_area, "window_area": window_area},
        "doors × height × width, windows × height × width"
    )
    
    # Step 3: Paintable area
    paintable_area = total_wall_area - door_area - window_area
    
    debugger.log_step(
        "Calculate Paintable Area",
        {"total_wall": total_wall_area, "door_area": door_area, "window_area": window_area},
        {"paintable_area": paintable_area},
        "total_wall - doors - windows"
    )
    
    # Step 4: Paint quantity
    paint_quantity_raw = (paintable_area * num_coats) / paint_coverage
    paint_quantity = paint_quantity_raw * wastage_factor
    
    debugger.log_step(
        "Calculate Paint Quantity",
        {
            "paintable_area": paintable_area,
            "coats": num_coats,
            "coverage": paint_coverage,
            "wastage": wastage_factor
        },
        {"raw_quantity": paint_quantity_raw, "with_wastage": round(paint_quantity, 2)},
        "(area × coats / coverage) × wastage_factor"
    )
    
    # Step 5: Paint cost
    paint_cost = paint_quantity * paint_price
    
    debugger.log_step(
        "Calculate Paint Cost",
        {"quantity": paint_quantity, "price": paint_price},
        {"cost": round(paint_cost, 2)},
        "quantity × price"
    )
    
    # Step 6: Putty quantity
    putty_quantity_raw = (paintable_area * 2) / putty_coverage  # 2 coats of putty
    putty_quantity = putty_quantity_raw * wastage_factor
    
    debugger.log_step(
        "Calculate Putty Quantity",
        {
            "paintable_area": paintable_area,
            "coats": 2,
            "coverage": putty_coverage,
            "wastage": wastage_factor
        },
        {"raw_quantity": putty_quantity_raw, "with_wastage": round(putty_quantity, 2)},
        "(area × 2 / coverage) × wastage_factor"
    )
    
    # Step 7: Putty cost
    putty_cost = putty_quantity * putty_price
    
    debugger.log_step(
        "Calculate Putty Cost",
        {"quantity": putty_quantity, "price": putty_price},
        {"cost": round(putty_cost, 2)},
        "quantity × price"
    )
    
    # Step 8: Total cost
    total_cost = paint_cost + putty_cost
    
    debugger.log_step(
        "Calculate Total Cost",
        {"paint_cost": round(paint_cost, 2), "putty_cost": round(putty_cost, 2)},
        {"total_cost": round(total_cost, 2)},
        "paint_cost + putty_cost"
    )
    
    return {
        "area_calculation": {
            "total_wall_area": round(total_wall_area, 2),
            "door_area": round(door_area, 2),
            "window_area": round(window_area, 2),
            "paintable_area": round(paintable_area, 2)
        },
        "quantities": {
            "paint_liters": round(paint_quantity, 2),
            "putty_kg": round(putty_quantity, 2)
        },
        "costs": {
            "paint_cost": round(paint_cost, 2),
            "putty_cost": round(putty_cost, 2),
            "total_cost": round(total_cost, 2)
        },
        "debug_report": debugger.generate_report(),
        "debug_json": debugger.export_json()
    }
