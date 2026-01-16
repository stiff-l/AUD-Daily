"""
Commodity Formatter Module

Standardizes commodity data structure and provides formatting utilities.
"""

from datetime import datetime
from typing import Dict, Any

# Import formatter utilities
try:
    from .formatter_utils import extract_date_from_data
except ImportError:
    from src.formatter_utils import extract_date_from_data


def standardize_commodity_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize commodity data structure to ensure consistent format.
    Handles: GOLD, SILVER, COPPER, ALUMINIUM, NICKEL
    
    Args:
        data: Raw data dictionary from collector
        
    Returns:
        Standardized data dictionary
    """
    standardized = {
        "date": None,
        "timestamp": datetime.now().isoformat(),
        "commodities": {}
    }
    
    # Extract date using shared utility
    standardized["date"] = extract_date_from_data(data, data_key="commodities")
    
    # Standardize commodities (GOLD, SILVER, COPPER, LITHIUM, IRON_ORE)
    if "commodities" in data:
        commodities_data = data["commodities"]
        # Check if commodities is nested (raw data) or direct (already standardized)
        if isinstance(commodities_data, dict) and "commodities" in commodities_data:
            commodities_data = commodities_data["commodities"]
        
        # If data is already standardized, copy commodities directly
        if isinstance(commodities_data, dict):
            for symbol, info in commodities_data.items():
                if isinstance(info, dict):
                    standardized["commodities"][symbol] = {
                        "price_aud": info.get("price_aud"),
                        "price_usd": info.get("price_usd"),
                        "unit": info.get("unit"),
                        "currency": info.get("currency", "AUD"),
                        "date": info.get("date", standardized["date"]),
                        "source": info.get("source", "unknown")
                    }
                else:
                    # Handle case where info might be a simple value
                    standardized["commodities"][symbol] = {
                        "price_aud": info,
                        "unit": "unknown",
                        "currency": "AUD",
                        "date": standardized["date"]
                    }
    
    return standardized
