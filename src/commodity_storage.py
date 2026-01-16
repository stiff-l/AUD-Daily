"""
Commodity Storage Module

Handles saving and loading commodity data to/from files and tables.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import formatter for standardization
try:
    from .commodity_formatter import standardize_commodity_data
except ImportError:
    try:
        from src.commodity_formatter import standardize_commodity_data
    except ImportError:
        # Fallback if formatter not available - use currency_formatter as backup
        try:
            from .currency_formatter import standardize_data as standardize_commodity_data
        except ImportError:
            from src.currency_formatter import standardize_data as standardize_commodity_data

# Import commodity history for table storage
try:
    from .commodity_history import upsert_commodity_history_row
except ImportError:
    try:
        from src.commodity_history import upsert_commodity_history_row
    except ImportError:
        upsert_commodity_history_row = None

# Import base storage utilities
try:
    from .base_storage import (
        ensure_directory_exists,
        save_raw_data_generic,
        save_daily_data_generic,
        load_data_generic,
        load_latest_data_generic
    )
except ImportError:
    from src.base_storage import (
        ensure_directory_exists,
        save_raw_data_generic,
        save_daily_data_generic,
        load_data_generic,
        load_latest_data_generic
    )


def save_raw_commodity_data(data: Dict[str, Any], output_dir: str = "data/commodities_data/raw") -> str:
    """
    Save raw commodity data to a JSON file.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    return save_raw_data_generic(data, output_dir, filename_prefix="commodity_data")


def save_daily_commodity_data(data: Dict[str, Any], output_dir: str = "data/commodities_data/processed") -> str:
    """
    Save daily commodity data with date-based filename.
    Data is standardized before saving to ensure consistent format.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    return save_daily_data_generic(
        data,
        output_dir,
        standardize_func=standardize_commodity_data,
        filename_prefix="commodity_daily"
    )


def load_commodity_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load commodity data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data dictionary, or None if file doesn't exist
    """
    return load_data_generic(filepath)


def load_latest_commodity_data(data_dir: str = "data/commodities_data/processed") -> Optional[Dict[str, Any]]:
    """
    Load the most recent commodity data file.
    
    Args:
        data_dir: Directory to search for data files
        
    Returns:
        Most recent data dictionary, or None if no files found
    """
    return load_latest_data_generic(data_dir, filename_pattern="commodity_daily_*.json")


def save_to_commodity_table(data: Dict[str, Any], csv_path: str = "data/commodities_data/processed/commodity_daily.csv") -> str:
    """
    Save commodity data to the daily table (CSV).
    Each day is a new row with timestamps for daily tracking.
    
    Args:
        data: Standardized data dictionary with commodities
        csv_path: Path to the daily commodity CSV file
        
    Returns:
        Path to the saved CSV file
    """
    if not upsert_commodity_history_row:
        print("Warning: commodity_history module not available. Skipping table save.")
        return csv_path
    
    try:
        # Standardize data if needed
        standardized_data = standardize_commodity_data(data)
        
        # Extract date
        date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            date_obj = datetime.now()
        
        # Extract timestamp
        timestamp_str = standardized_data.get("timestamp")
        if timestamp_str:
            try:
                timestamp_obj = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except:
                timestamp_obj = datetime.now()
        else:
            timestamp_obj = datetime.now()
        
        # Extract commodity prices
        commodities = standardized_data.get("commodities", {})
        gold_price = commodities.get("GOLD", {}).get("price_aud") if commodities.get("GOLD") else None
        silver_price = commodities.get("SILVER", {}).get("price_aud") if commodities.get("SILVER") else None
        copper_price = commodities.get("COPPER", {}).get("price_aud") if commodities.get("COPPER") else None
        aluminium_price = commodities.get("ALUMINIUM", {}).get("price_aud") if commodities.get("ALUMINIUM") else None
        nickel_price = commodities.get("NICKEL", {}).get("price_aud") if commodities.get("NICKEL") else None
        
        # Save to CSV
        upsert_commodity_history_row(
            csv_path=csv_path,
            date=date_obj,
            gold_price=gold_price,
            silver_price=silver_price,
            copper_price=copper_price,
            aluminium_price=aluminium_price,
            nickel_price=nickel_price,
            timestamp=timestamp_obj
        )
        
        # Verify the CSV was created/updated
        if os.path.exists(csv_path):
            print(f"✓ Commodity data saved to table: {csv_path}")
        else:
            print(f"⚠ Warning: CSV file was not created at {csv_path}")
        
        return csv_path
    except Exception as e:
        print(f"❌ Error saving to commodity table: {e}")
        import traceback
        traceback.print_exc()
        raise
