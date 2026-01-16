#!/usr/bin/env python3
"""
Update CSV files from processed JSON data.
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.currency_storage import save_to_currency_table
from src.currency_formatter import standardize_data

def update_csv_from_json(json_path: str):
    """Update CSV files from a processed JSON file."""
    # Load the processed data
    with open(json_path, 'r', encoding='utf-8') as f:
        processed_data = json.load(f)
    
    # Ensure data is standardized
    standardized_data = standardize_data(processed_data)
    
    # Save to both CSV files
    print(f'Updating CSV files from {json_path}...')
    save_to_currency_table(standardized_data)
    print('✓ CSV files updated successfully')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python update_csv_from_json.py <json_path>')
        sys.exit(1)
    
    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f'Error: File not found: {json_path}')
        sys.exit(1)
    
    update_csv_from_json(json_path)
