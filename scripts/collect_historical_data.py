#!/usr/bin/env python3
"""
Historical Data Collection Script

Collect quarterly AUD exchange rate data since modern AUD creation (1966).
This script fetches historical data and stores it for analysis.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import collect_historical_quarterly_data
from src.data_storage import ensure_directory_exists, save_raw_data
import json


def main():
    """Main function to collect historical quarterly data."""
    print("=" * 60)
    print("AUD Historical Data Collection - Quarterly Data Since 1966")
    print("=" * 60)
    print()
    
    # Collect historical data
    print("Starting historical data collection...")
    print("Note: This will take several minutes due to API rate limits.")
    print()
    
    historical_data = collect_historical_quarterly_data(start_year=1966)
    
    # Save to historical data directory
    historical_dir = "data/historical"
    ensure_directory_exists(historical_dir)
    
    # Save as JSON file
    filename = f"aud_historical_quarterly_{historical_data['start_year']}_to_{historical_data['end_year']}.json"
    filepath = os.path.join(historical_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(historical_data, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"Historical data saved to: {filepath}")
    print("=" * 60)
    
    # Print summary
    print("\nSummary:")
    for currency, rates in historical_data["currencies"].items():
        print(f"  {currency}: {len(rates)} data points")
    
    print("\nData collection complete!")


if __name__ == "__main__":
    main()

