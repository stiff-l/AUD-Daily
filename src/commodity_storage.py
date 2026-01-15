"""
Commodity Storage Module

Handles saving and loading commodity data to/from files and tables.
"""

import json
import os
from datetime import datetime
from pathlib import Path
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


def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def save_raw_commodity_data(data: Dict[str, Any], output_dir: str = "data/commodities_data/raw") -> str:
    """
    Save raw commodity data to a JSON file.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    ensure_directory_exists(output_dir)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"commodity_data_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Commodity data saved to: {filepath}")
    return filepath


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
    ensure_directory_exists(output_dir)
    
    # Standardize data structure before saving
    standardized_data = standardize_commodity_data(data)
    
    # Create filename with date only
    date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
    filename = f"commodity_daily_{date_str}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(standardized_data, f, indent=2, ensure_ascii=False)
    
    print(f"Daily commodity data saved to: {filepath}")
    return filepath


def load_commodity_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load commodity data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data dictionary, or None if file doesn't exist
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        return None


def load_latest_commodity_data(data_dir: str = "data/commodities_data/processed") -> Optional[Dict[str, Any]]:
    """
    Load the most recent commodity data file.
    
    Args:
        data_dir: Directory to search for data files
        
    Returns:
        Most recent data dictionary, or None if no files found
    """
    if not os.path.exists(data_dir):
        return None
    
    # Find all JSON files
    json_files = list(Path(data_dir).glob("commodity_daily_*.json"))
    
    if not json_files:
        return None
    
    # Get the most recent file
    latest_file = max(json_files, key=os.path.getctime)
    return load_commodity_data(str(latest_file))


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
        zinc_price = commodities.get("ZINC", {}).get("price_aud") if commodities.get("ZINC") else None
        nickel_price = commodities.get("NICKEL", {}).get("price_aud") if commodities.get("NICKEL") else None
        
        # Save to CSV
        upsert_commodity_history_row(
            csv_path=csv_path,
            date=date_obj,
            gold_price=gold_price,
            silver_price=silver_price,
            copper_price=copper_price,
            aluminium_price=aluminium_price,
            zinc_price=zinc_price,
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
