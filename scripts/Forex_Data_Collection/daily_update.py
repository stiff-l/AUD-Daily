#!/usr/bin/env python3
"""
Daily Update Script

Run this script daily to collect and save AUD currency tracking data.
Tracks: USD, EUR, CNY, SGD, JPY
Can be run manually or scheduled with cron (Linux/Mac) or Task Scheduler (Windows).

Designed to run at 5pm Cairns time (AEST - UTC+10) for COB updates.
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.currency_collector import collect_all_data
from src.currency_storage import save_raw_data, save_daily_data, save_to_currency_table
from src.currency_formatter import standardize_data
from scripts.generate_forex_html import generate_forex_html
from scripts.cleanup_raw_files import cleanup_raw_files

# Import update utilities
try:
    from ..update_utils import get_cairns_time, is_cob_time
except ImportError:
    try:
        from scripts.update_utils import get_cairns_time, is_cob_time
    except ImportError:
        # Fallback - import from parent directory
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from scripts.update_utils import get_cairns_time, is_cob_time


def main():
    """Main function to run daily data collection."""
    print("=" * 60)
    print("AUD Daily Tracker - Currency Data Collection")
    print("Tracking: USD, EUR, CNY, SGD, JPY")
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
        save_raw_data(data, output_dir="data/forex_data/raw")
        
        # Cleanup raw files (keep max 2 per date)
        try:
            print("Cleaning up old raw files...")
            cleanup_raw_files(verbose=False)
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
            # Don't fail the update if cleanup fails
        
        # Save daily data (date-based filename, overwrites if exists)
        print("Saving daily data...")
        save_daily_data(standardized_data, output_dir="data/forex_data/processed")
        
        # Save to currency history table (CSV)
        print("Saving to currency history table...")
        save_to_currency_table(standardized_data)
        
        # Generate forex HTML from template (data comes from API)
        try:
            print("\nGenerating forex HTML...")
            template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'forex_template.html')
            if os.path.exists(template_path):
                generate_forex_html(template_path, output_dir="data/forex_data", standardized_data=standardized_data)
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

