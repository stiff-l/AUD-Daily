"""
Commodity Collector Module

This module handles fetching mineral commodity prices from TradingEconomics.com.
Tracks: Gold, Silver, Copper, Aluminium, Nickel in AUD.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TradingEconomics scraper
try:
    from .tradingeconomics_scraper import scrape_all_commodities
except ImportError:
    try:
        from src.tradingeconomics_scraper import scrape_all_commodities
    except ImportError:
        # Fallback - import from same directory
        scraper_path = os.path.join(os.path.dirname(__file__), "tradingeconomics_scraper.py")
        try:
            from .import_utils import safe_import_module, get_module_attribute
        except ImportError:
            from src.import_utils import safe_import_module, get_module_attribute
        
        tradingeconomics_module = safe_import_module(
            "tradingeconomics_scraper",
            package_name="src",
            fallback_path=scraper_path
        )
        if tradingeconomics_module:
            scrape_all_commodities = get_module_attribute(tradingeconomics_module, "scrape_all_commodities")
        else:
            raise ImportError(f"Could not import tradingeconomics_scraper from any location")


def fetch_commodity_prices() -> Dict[str, Any]:
    """
    Fetch mineral commodity prices in AUD from TradingEconomics.
    Tracks: Gold, Silver, Copper, Aluminium, Nickel.
    
    Returns:
        Dictionary with commodity prices and metadata
    """
    # Use the TradingEconomics scraper
    return scrape_all_commodities()


def collect_all_commodity_data() -> Dict[str, Any]:
    """
    Collect all commodity data (Gold, Silver, Copper, Aluminium, Nickel).
    
    Returns:
        Dataset with commodity prices
    """
    print("Collecting commodity prices from TradingEconomics...")
    data = fetch_commodity_prices()
    
    return {
        "collection_date": datetime.now().isoformat(),
        "commodities": data
    }


if __name__ == "__main__":
    # Test the data collection
    print("Testing commodity data collection...")
    data = collect_all_commodity_data()
    print("\nCollected Data:")
    print(json.dumps(data, indent=2))
