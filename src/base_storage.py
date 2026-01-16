"""
Base Storage Module

Generic storage functions that can be used by both currency and commodity storage modules.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable


def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def save_raw_data_generic(
    data: Dict[str, Any],
    output_dir: str,
    filename_prefix: str = "data"
) -> str:
    """
    Save raw data to a JSON file with timestamp.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        filename_prefix: Prefix for the filename (e.g., "aud_data" or "commodity_data")
        
    Returns:
        Path to the saved file
    """
    ensure_directory_exists(output_dir)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to: {filepath}")
    return filepath


def save_daily_data_generic(
    data: Dict[str, Any],
    output_dir: str,
    standardize_func: Callable[[Dict[str, Any]], Dict[str, Any]],
    filename_prefix: str = "daily"
) -> str:
    """
    Save daily data with date-based filename.
    Data is standardized before saving to ensure consistent format.
    
    Args:
        data: The data dictionary to save
        output_dir: Directory to save the file
        standardize_func: Function to standardize the data
        filename_prefix: Prefix for the filename (e.g., "aud_daily" or "commodity_daily")
        
    Returns:
        Path to the saved file
    """
    ensure_directory_exists(output_dir)
    
    # Standardize data structure before saving
    standardized_data = standardize_func(data)
    
    # Create filename with date only
    date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
    filename = f"{filename_prefix}_{date_str}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(standardized_data, f, indent=2, ensure_ascii=False)
    
    print(f"Daily data saved to: {filepath}")
    return filepath


def load_data_generic(filepath: str) -> Optional[Dict[str, Any]]:
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


def load_latest_data_generic(
    data_dir: str,
    filename_pattern: str = "daily_*.json"
) -> Optional[Dict[str, Any]]:
    """
    Load the most recent data file matching the pattern.
    
    Args:
        data_dir: Directory to search for data files
        filename_pattern: Glob pattern to match files (e.g., "aud_daily_*.json" or "commodity_daily_*.json")
        
    Returns:
        Most recent data dictionary, or None if no files found
    """
    if not os.path.exists(data_dir):
        return None
    
    # Find all JSON files matching the pattern
    json_files = list(Path(data_dir).glob(filename_pattern))
    
    if not json_files:
        return None
    
    # Get the most recent file
    latest_file = max(json_files, key=os.path.getctime)
    return load_data_generic(str(latest_file))
