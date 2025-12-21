#!/usr/bin/env python3
"""
Daily Update Script

Run this script daily to collect and save AUD tracking data.
Can be scheduled with cron (Linux/Mac) or Task Scheduler (Windows).
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import collect_all_data
from src.data_storage import save_raw_data, save_daily_data


def main():
    """Main function to run daily data collection."""
    print("=" * 50)
    print("AUD Daily Tracker - Data Collection")
    print("=" * 50)
    
    # Collect all data
    data = collect_all_data()
    
    # Save raw data (with timestamp)
    save_raw_data(data, output_dir="data/raw")
    
    # Save daily data (date-based filename, overwrites if exists)
    save_daily_data(data, output_dir="data/processed")
    
    print("\n" + "=" * 50)
    print("Data collection complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()

