"""Response utilities for API responses."""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
    
    Returns:
        Formatted response dictionary
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "status_code": status_code
    }


def error_response(
    message: str,
    error_code: Optional[str] = None,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an error response.
    
    Args:
        message: Error message
        error_code: Optional error code
        status_code: HTTP status code
        details: Optional error details
    
    Returns:
        Formatted error response dictionary
    """
    response = {
        "success": False,
        "message": message,
        "status_code": status_code
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response


def validate_positive_number(value: float, field_name: str) -> None:
    """
    Validate that a number is positive.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
    
    Raises:
        HTTPException: If value is not positive
    """
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a positive number"
        )


def validate_non_negative_integer(value: int, field_name: str) -> None:
    """
    Validate that an integer is non-negative.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
    
    Raises:
        HTTPException: If value is negative
    """
    if value < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a non-negative integer"
        )


def format_currency(amount: float, currency: str = "₹") -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
    
    Returns:
        Formatted currency string
    """
    return f"{currency}{amount:,.2f}"


def format_quantity(quantity: float, unit: str) -> str:
    """
    Format quantity with unit.
    
    Args:
        quantity: Quantity value
        unit: Unit of measurement
    
    Returns:
        Formatted quantity string
    """
    return f"{quantity:.2f} {unit}"
