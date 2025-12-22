"""
Data Storage Module

Handles saving and loading data to/from files.
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
    try:
        from src.data_formatter import standardize_data
    except ImportError:
        # Fallback if import fails
        def standardize_data(data: Dict[str, Any]) -> Dict[str, Any]:
            return data


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

