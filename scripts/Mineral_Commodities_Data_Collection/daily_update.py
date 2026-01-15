#!/usr/bin/env python3
"""
Daily Update Script for Mineral Commodities

Run this script daily to collect and save mineral commodity tracking data.
Tracks: Gold, Silver, Copper, Lithium, Iron Ore
Can be run manually or scheduled with cron (Linux/Mac) or Task Scheduler (Windows).

Designed to run at 5pm Cairns time (AEST - UTC+10) for COB updates.
"""

import sys
import os
from datetime import datetime
import pytz

# Add project root to path (go up two levels from scripts/Mineral_Commodities_Data_Collection/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.commodity_collector import collect_all_commodity_data
from src.commodity_storage import save_raw_commodity_data, save_daily_commodity_data, save_to_commodity_table
from src.commodity_formatter import standardize_commodity_data
from scripts.generate_mineral_commodities_html import generate_mineral_commodities_html


def get_cairns_time():
    """
    Get current time in Cairns (AEST - UTC+10, no daylight saving).
    
    Returns:
        datetime object in AEST timezone
    """
    # Cairns is in Queensland, which uses AEST (UTC+10) year-round
    cairns_tz = pytz.timezone('Australia/Brisbane')  # Brisbane uses same timezone as Cairns
    return datetime.now(cairns_tz)


def is_cob_time():
    """
    Check if current time is close to COB (5pm Cairns time).
    
    Returns:
        True if within 1 hour of 5pm AEST, False otherwise
    """
    cairns_time = get_cairns_time()
    hour = cairns_time.hour
    
    # Check if it's around 5pm (17:00) - allow 1 hour window
    return 16 <= hour <= 18


def main():
    """Main function to run daily commodity data collection."""
    print("=" * 60)
    print("AUD Daily Tracker - Mineral Commodities Data Collection")
    print("Tracking: Gold, Silver, Copper, Aluminium, Zinc, Nickel")
    print("=" * 60)
    
    cairns_time = get_cairns_time()
    print(f"Current Cairns time: {cairns_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Target time: 5:00 PM AEST (COB)")
    print()
    
    # Check if it's COB time (optional - can be run manually anytime)
    if not is_cob_time():
        print("Note: Not currently COB time, but proceeding with update...")
        print()
    
    try:
        # Collect commodity data
        print("Collecting commodity prices...")
        data = collect_all_commodity_data()
        
        # Standardize data
        standardized_data = standardize_commodity_data(data)
        
        # Save raw data (with timestamp)
        print("\nSaving raw data...")
        save_raw_commodity_data(data, output_dir="data/commodities_data/raw")
        
        # Save daily data (date-based filename, overwrites if exists)
        print("Saving daily data...")
        save_daily_commodity_data(standardized_data, output_dir="data/commodities_data/processed")
        
        # Save to commodity history table (CSV)
        print("Saving to commodity history table...")
        save_to_commodity_table(standardized_data)
        
        # Generate mineral commodities HTML from template
        try:
            print("\nGenerating mineral commodities HTML...")
            template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'mineral_commodities_template.html')
            if os.path.exists(template_path):
                generate_mineral_commodities_html(template_path, output_dir="data/commodities_data", standardized_data=standardized_data)
            else:
                print(f"Warning: Template not found at {template_path}, skipping HTML generation.")
        except Exception as e:
            print(f"Warning: Error generating HTML: {e}")
            # Don't fail the entire update if HTML generation fails
        
        print("\n" + "=" * 60)
        print("Data collection complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during data collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
