#!/usr/bin/env python3
"""
Daily Update Script

Run this script daily to collect and save AUD currency tracking data.
Tracks: USD, EUR, CNY, SGD
Can be scheduled with cron (Linux/Mac) or Task Scheduler (Windows).

Note: For scheduled updates at 5pm Cairns time, use scripts/scheduled_update.py instead.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import collect_all_data
from src.data_storage import save_raw_data, save_daily_data, save_to_currency_table
from src.data_formatter import standardize_data
from scripts.generate_forex_svg import generate_forex_svg


def main():
    """Main function to run daily data collection."""
    print("=" * 50)
    print("AUD Daily Tracker - Currency Data Collection")
    print("Tracking: USD, EUR, CNY, SGD")
    print("=" * 50)
    
    # Collect currency data
    data = collect_all_data()
    
    # Standardize data
    standardized_data = standardize_data(data)
    
    # Save raw data (with timestamp)
    save_raw_data(data, output_dir="data/raw")
    
    # Save daily data (date-based filename, overwrites if exists)
    save_daily_data(standardized_data, output_dir="data/processed")
    
    # Save to currency history table (CSV)
    save_to_currency_table(standardized_data)
    
    # Generate forex SVG from template
    try:
        print("\nGenerating forex SVG...")
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'forex_template.svg')
        if os.path.exists(template_path):
            generate_forex_svg(template_path, output_dir="data/forex_data", standardized_data=standardized_data)
        else:
            print(f"Warning: Template not found at {template_path}, skipping SVG generation.")
    except Exception as e:
        print(f"Warning: Error generating SVG: {e}")
        # Don't fail the entire update if SVG generation fails
    
    print("\n" + "=" * 50)
    print("Data collection complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()

