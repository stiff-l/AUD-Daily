"""
Formatter Utilities Module

Shared utilities for data formatting used by both currency and commodity formatters.
"""

from datetime import datetime
from typing import Dict, Any, Optional


def extract_date_from_data(data: Dict[str, Any], data_key: str = "currencies") -> Optional[str]:
    """
    Extract date from data dictionary, handling various data structures.
    
    This function handles:
    1. Direct 'date' field in data
    2. Date from nested data structures (e.g., currencies/commodities)
    3. collection_date field
    4. Falls back to current date
    
    Args:
        data: Raw data dictionary
        data_key: Key to look for nested data (e.g., "currencies" or "commodities")
        
    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    # If data already has a 'date' field (already standardized), use it
    if "date" in data and data["date"]:
        return data["date"]
    
    # Extract date from nested data first (for historical dates)
    historical_date = None
    if data_key in data:
        nested_data = data[data_key]
        if isinstance(nested_data, dict) and data_key in nested_data:
            # Double-nested structure (e.g., {"currencies": {"currencies": {...}}})
            nested_data = nested_data[data_key]
        
        # Get the date from the first item that has a date
        if isinstance(nested_data, dict):
            for symbol, info in nested_data.items():
                if isinstance(info, dict) and "date" in info:
                    historical_date = info.get("date")
                    break
    
    # Use historical date if found
    if historical_date:
        return historical_date
    
    # Try collection_date
    if "collection_date" in data:
        try:
            date_obj = datetime.fromisoformat(data["collection_date"].replace("Z", "+00:00"))
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass
    
    # Fall back to current date
    return datetime.now().strftime("%Y-%m-%d")
