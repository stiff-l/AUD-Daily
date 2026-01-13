#!/usr/bin/env python3
"""
Scheduled Update Script

Runs daily data collection at 5pm Cairns time (AEST - UTC+10).
Can be run manually or scheduled with cron/scheduler.
"""

import sys
import os
from datetime import datetime
import pytz

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import collect_all_data
from src.data_storage import save_raw_data, save_daily_data, save_to_currency_table
from src.data_formatter import standardize_data
from scripts.generate_forex_html import generate_forex_html


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
    """Main function to run scheduled data collection at 5pm Cairns time."""
    print("=" * 60)
    print("AUD Daily Tracker - Scheduled Update")
    print("Tracking: USD, EUR, CNY, SGD")
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
        # Collect currency data
        print("Collecting currency data...")
        data = collect_all_data()
        
        # Standardize data
        standardized_data = standardize_data(data)
        
        # Save raw data (with timestamp)
        print("\nSaving raw data...")
        save_raw_data(data, output_dir="data/raw")
        
        # Save daily data (date-based filename)
        print("Saving daily data...")
        save_daily_data(standardized_data, output_dir="data/processed")
        
        # Save to currency history table (CSV)
        print("Saving to currency history table...")
        save_to_currency_table(standardized_data)
        
        # Generate forex HTML from template (data comes from API)
        try:
            print("\nGenerating forex HTML...")
            template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'forex_template.html')
            if os.path.exists(template_path):
                generate_forex_html(template_path, output_dir="data/forex_data", standardized_data=standardized_data)
            else:
                print(f"Warning: Template not found at {template_path}, skipping HTML generation.")
        except Exception as e:
            print(f"Warning: Error generating HTML: {e}")
            # Don't fail the entire update if HTML generation fails
        
        print("\n" + "=" * 60)
        print("Scheduled update complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during scheduled update: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

