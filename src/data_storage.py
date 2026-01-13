"""
Data Storage Module

Handles saving and loading data to/from files and tables.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import formatter for standardization
try:
    from .data_formatter import standardize_data
except ImportError:
    from src.data_formatter import standardize_data

# Import currency history for table storage
try:
    from .currency_history import upsert_currency_history_row
except ImportError:
    try:
        from src.currency_history import upsert_currency_history_row
    except ImportError:
        upsert_currency_history_row = None


def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def save_raw_data(data: Dict[str, Any], output_dir: str = "data/raw") -> str:
    """
    Save raw data to a JSON file.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    ensure_directory_exists(output_dir)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aud_data_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to: {filepath}")
    return filepath


def save_daily_data(data: Dict[str, Any], output_dir: str = "data/processed") -> str:
    """
    Save daily data with date-based filename.
    Data is standardized before saving to ensure consistent format.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    ensure_directory_exists(output_dir)
    
    # Standardize data structure before saving
    standardized_data = standardize_data(data)
    
    # Create filename with date only
    date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
    filename = f"aud_daily_{date_str}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(standardized_data, f, indent=2, ensure_ascii=False)
    
    print(f"Daily data saved to: {filepath}")
    return filepath


def load_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
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


def load_latest_data(data_dir: str = "data/processed") -> Optional[Dict[str, Any]]:
    """
    Load the most recent data file.
    
    Args:
        data_dir: Directory to search for data files
        
    Returns:
        Most recent data dictionary, or None if no files found
    """
    if not os.path.exists(data_dir):
        return None
    
    # Find all JSON files
    json_files = list(Path(data_dir).glob("aud_daily_*.json"))
    
    if not json_files:
        return None
    
    # Get the most recent file
    latest_file = max(json_files, key=os.path.getctime)
    return load_data(str(latest_file))


def save_to_currency_table(data: Dict[str, Any], csv_path: str = "data/processed/currency_daily.csv") -> str:
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
            csv_path,  # Daily CSV: data/processed/currency_daily.csv
            "data/historical/currency_history.csv"  # Historical CSV
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

