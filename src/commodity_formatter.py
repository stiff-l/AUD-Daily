"""
Commodity Formatter Module

Standardizes commodity data structure and provides formatting utilities.
"""

from datetime import datetime
from typing import Dict, Any


def standardize_commodity_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize commodity data structure to ensure consistent format.
    Handles: GOLD, SILVER, COPPER, ALUMINIUM, ZINC, NICKEL
    
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
    
    # If data already has a 'date' field (already standardized), use it
    if "date" in data and data["date"]:
        standardized["date"] = data["date"]
    
    # Extract date from commodity data first (for historical dates)
    # Then fall back to collection_date or current date
    historical_date = None
    if not standardized["date"] and "commodities" in data:
        commodities_data = data["commodities"]
        if isinstance(commodities_data, dict) and "commodities" in commodities_data:
            commodities_data = commodities_data["commodities"]
            # Get the date from the first commodity that has a date
            for symbol, info in commodities_data.items():
                if isinstance(info, dict) and "date" in info:
                    historical_date = info.get("date")
                    break
        else:
            # Data might already be standardized - check commodities directly
            for symbol, info in commodities_data.items():
                if isinstance(info, dict) and "date" in info:
                    historical_date = info.get("date")
                    break
    
    # Use historical date if found, otherwise use collection_date or current date
    if not standardized["date"]:
        if historical_date:
            standardized["date"] = historical_date
        elif "collection_date" in data:
            try:
                date_obj = datetime.fromisoformat(data["collection_date"].replace("Z", "+00:00"))
                standardized["date"] = date_obj.strftime("%Y-%m-%d")
            except:
                standardized["date"] = datetime.now().strftime("%Y-%m-%d")
        else:
            standardized["date"] = datetime.now().strftime("%Y-%m-%d")
    
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
