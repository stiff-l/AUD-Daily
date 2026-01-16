"""
Currency Storage Module

Handles saving and loading data to/from files and tables.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import formatter for standardization
try:
    from .currency_formatter import standardize_data
except ImportError:
    from src.currency_formatter import standardize_data

# Import currency history for table storage
try:
    from .currency_history import upsert_currency_history_row
except ImportError:
    try:
        from src.currency_history import upsert_currency_history_row
    except ImportError:
        upsert_currency_history_row = None

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


def save_raw_data(data: Dict[str, Any], output_dir: str = "data/forex_data/raw") -> str:
    """
    Save raw data to a JSON file.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    return save_raw_data_generic(data, output_dir, filename_prefix="aud_data")


def save_daily_data(data: Dict[str, Any], output_dir: str = "data/forex_data/processed") -> str:
    """
    Save daily data with date-based filename.
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
        standardize_func=standardize_data,
        filename_prefix="aud_daily"
    )


def load_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data dictionary, or None if file doesn't exist
    """
    return load_data_generic(filepath)


def load_latest_data(data_dir: str = "data/forex_data/processed") -> Optional[Dict[str, Any]]:
    """
    Load the most recent data file.
    
    Args:
        data_dir: Directory to search for data files
        
    Returns:
        Most recent data dictionary, or None if no files found
    """
    return load_latest_data_generic(data_dir, filename_pattern="aud_daily_*.json")


def save_to_currency_table(data: Dict[str, Any], csv_path: str = "data/forex_data/processed/currency_daily.csv") -> str:
    """
    Save currency data to the daily table (CSV).
    Each day is a new row with timestamps for daily tracking.
    
    Args:
        data: Standardized data dictionary with currencies
        csv_path: Path to the daily currency CSV file
        
    Returns:
        Path to the saved CSV file
    """
    if not upsert_currency_history_row:
        print("Warning: currency_history module not available. Skipping table save.")
        return csv_path
    
    try:
        # Standardize data if needed
        standardized_data = standardize_data(data)
        
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
        
        # Extract currency rates
        currencies = standardized_data.get("currencies", {})
        usd_rate = currencies.get("USD", {}).get("rate") if currencies.get("USD") else None
        eur_rate = currencies.get("EUR", {}).get("rate") if currencies.get("EUR") else None
        cny_rate = currencies.get("CNY", {}).get("rate") if currencies.get("CNY") else None
        sgd_rate = currencies.get("SGD", {}).get("rate") if currencies.get("SGD") else None
        jpy_rate = currencies.get("JPY", {}).get("rate") if currencies.get("JPY") else None
        
        # Save to both CSV files
        csv_paths = [
            csv_path,  # Daily CSV: data/forex_data/processed/currency_daily.csv
            "data/forex_data/historical/currency_history.csv"  # Historical CSV
        ]
        
        saved_paths = []
        for path in csv_paths:
            try:
                upsert_currency_history_row(
                    csv_path=path,
                    date=date_obj,
                    usd_rate=usd_rate,
                    eur_rate=eur_rate,
                    cny_rate=cny_rate,
                    sgd_rate=sgd_rate,
                    jpy_rate=jpy_rate,
                    timestamp=timestamp_obj
                )
                
                # Verify the CSV was created/updated
                if os.path.exists(path):
                    print(f"✓ Currency data saved to table: {path}")
                    saved_paths.append(path)
                else:
                    print(f"⚠ Warning: CSV file was not created at {path}")
            except Exception as e:
                print(f"⚠ Warning: Error saving to {path}: {e}")
        
        return csv_path if saved_paths else csv_paths[0]
    except Exception as e:
        print(f"❌ Error saving to currency table: {e}")
        import traceback
        traceback.print_exc()
        raise

