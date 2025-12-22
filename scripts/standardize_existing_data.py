#!/usr/bin/env python3
"""
Standardize Existing Data Script

Convert existing JSON files to the standardized format.
"""

import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_formatter import standardize_data
from src.data_storage import load_data


def standardize_file(filepath: str, backup: bool = True) -> bool:
    """
    Standardize a single data file.
    
    Args:
        filepath: Path to the JSON file
        backup: Whether to create a backup before modifying
        
    Returns:
        True if successful, False otherwise
    """
    # Load existing data
    data = load_data(filepath)
    if not data:
        print(f"Error: Could not load {filepath}")
        return False
    
    # Standardize
    standardized = standardize_data(data)
    
    # Create backup if requested
    if backup:
        backup_path = filepath + ".backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(filepath, backup_path)
            print(f"Created backup: {backup_path}")
    
    # Save standardized version
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(standardized, f, indent=2, ensure_ascii=False)
    
    print(f"Standardized: {filepath}")
    return True


def main():
    """Standardize all existing data files."""
    processed_dir = "data/processed"
    
    if not os.path.exists(processed_dir):
        print(f"Directory not found: {processed_dir}")
        return
    
    # Find all JSON files
    json_files = list(Path(processed_dir).glob("aud_daily_*.json"))
    
    if not json_files:
        print(f"No data files found in {processed_dir}")
        return
    
    print(f"Found {len(json_files)} files to standardize")
    print("-" * 60)
    
    for filepath in sorted(json_files):
        standardize_file(str(filepath))
    
    print("-" * 60)
    print("Standardization complete!")


if __name__ == "__main__":
    main()

