#!/usr/bin/env python3
"""
Collect Raw and Processed Data JSON for Missed Dates

This script identifies dates that are missing raw or processed JSON data files
and collects historical data for those dates.

Usage:
    python scripts/collect_missed_dates.py --start-date 2025-01-01 --end-date 2025-12-31
    python scripts/collect_missed_dates.py --start-date 2025-01-01 --end-date 2025-12-31 --check-raw-only
    python scripts/collect_missed_dates.py --start-date 2025-01-01 --end-date 2025-12-31 --check-processed-only
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import collect_historical_data_for_date
from src.data_storage import save_raw_data, save_daily_data, save_to_currency_table
from src.data_formatter import standardize_data


def get_existing_dates(data_dir: str, file_prefix: str) -> set:
    """
    Get set of dates that already have data files.
    
    Args:
        data_dir: Directory to check (e.g., "data/raw" or "data/processed")
        file_prefix: Prefix of files to check (e.g., "aud_data_" or "aud_daily_")
        
    Returns:
        Set of date strings in YYYY-MM-DD format
    """
    existing_dates = set()
    
    if not os.path.exists(data_dir):
        return existing_dates
    
    # For raw data: files are like "aud_data_20250101_120000.json"
    # Extract date from timestamp
    if file_prefix == "aud_data_":
        for filepath in Path(data_dir).glob("aud_data_*.json"):
            # Extract date from filename: aud_data_YYYYMMDD_HHMMSS.json
            filename = filepath.stem
            try:
                date_part = filename.split("_")[2]  # Get YYYYMMDD part
                date_obj = datetime.strptime(date_part, "%Y%m%d")
                existing_dates.add(date_obj.strftime("%Y-%m-%d"))
            except (IndexError, ValueError):
                continue
    
    # For processed data: files are like "aud_daily_2025-01-01.json"
    elif file_prefix == "aud_daily_":
        for filepath in Path(data_dir).glob("aud_daily_*.json"):
            # Extract date from filename: aud_daily_YYYY-MM-DD.json
            filename = filepath.stem
            try:
                date_part = filename.replace("aud_daily_", "")
                date_obj = datetime.strptime(date_part, "%Y-%m-%d")
                existing_dates.add(date_obj.strftime("%Y-%m-%d"))
            except ValueError:
                continue
    
    return existing_dates


def get_missed_dates(start_date: str, end_date: str, 
                     check_raw: bool = True, check_processed: bool = True) -> list:
    """
    Identify dates that are missing data files.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        check_raw: Whether to check for raw data files
        check_processed: Whether to check for processed data files
        
    Returns:
        List of date strings in YYYY-MM-DD format that are missing
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Get all dates in range
    all_dates = set()
    current = start
    while current <= end:
        all_dates.add(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    # Get existing dates
    existing_dates = set()
    
    if check_raw:
        raw_dates = get_existing_dates("data/raw", "aud_data_")
        existing_dates.update(raw_dates)
    
    if check_processed:
        processed_dates = get_existing_dates("data/processed", "aud_daily_")
        existing_dates.update(processed_dates)
    
    # Find missed dates
    missed_dates = sorted(all_dates - existing_dates)
    
    return missed_dates


def collect_data_for_date(date: str, save_raw: bool = True, 
                         save_processed: bool = True, save_csv: bool = True) -> bool:
    """
    Collect and save data for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        save_raw: Whether to save raw data JSON
        save_processed: Whether to save processed data JSON
        save_csv: Whether to save to CSV table
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"\nCollecting data for {date}...")
        
        # Collect historical data
        raw_data = collect_historical_data_for_date(date)
        
        # Check if we got any currency data
        currencies = raw_data.get("currencies", {}).get("currencies", {})
        if not currencies:
            print(f"  ⚠ Warning: No currency data collected for {date}")
            return False
        
        # Save raw data
        if save_raw:
            save_raw_data(raw_data, output_dir="data/raw")
        
        # Standardize and save processed data
        if save_processed or save_csv:
            standardized_data = standardize_data(raw_data)
            
            if save_processed:
                save_daily_data(standardized_data, output_dir="data/processed")
            
            if save_csv:
                try:
                    save_to_currency_table(standardized_data)
                except Exception as e:
                    print(f"  ⚠ Warning: Error saving to CSV: {e}")
        
        print(f"  ✓ Successfully collected data for {date}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error collecting data for {date}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to collect data for missed dates."""
    parser = argparse.ArgumentParser(
        description="Collect raw and processed data JSON for missed dates"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--check-raw-only",
        action="store_true",
        help="Only check for missing raw data files"
    )
    parser.add_argument(
        "--check-processed-only",
        action="store_true",
        help="Only check for missing processed data files"
    )
    parser.add_argument(
        "--skip-raw",
        action="store_true",
        help="Don't save raw data JSON files"
    )
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="Don't save processed data JSON files"
    )
    parser.add_argument(
        "--skip-csv",
        action="store_true",
        help="Don't save to CSV table"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between API calls in seconds (default: 0.5)"
    )
    
    args = parser.parse_args()
    
    # Validate dates
    try:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
        end = datetime.strptime(args.end_date, "%Y-%m-%d")
        if start > end:
            print("Error: Start date must be before or equal to end date")
            return 1
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD format. {e}")
        return 1
    
    # Determine what to check
    check_raw = not args.check_processed_only
    check_processed = not args.check_raw_only
    
    print("=" * 70)
    print("AUD Daily Tracker - Collect Missed Dates")
    print("=" * 70)
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Checking: {'Raw' if check_raw else ''} {'Processed' if check_processed else ''}")
    print("=" * 70)
    
    # Find missed dates
    print("\nIdentifying missed dates...")
    missed_dates = get_missed_dates(
        args.start_date, 
        args.end_date,
        check_raw=check_raw,
        check_processed=check_processed
    )
    
    if not missed_dates:
        print("✓ No missed dates found. All dates in range have data files.")
        return 0
    
    print(f"Found {len(missed_dates)} missed date(s):")
    if len(missed_dates) <= 20:
        for date in missed_dates:
            print(f"  - {date}")
    else:
        print(f"  First 10: {', '.join(missed_dates[:10])}")
        print(f"  ... and {len(missed_dates) - 10} more")
    
    # Confirm before proceeding
    response = input(f"\nProceed with collecting data for {len(missed_dates)} date(s)? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0
    
    # Collect data for each missed date
    print("\n" + "=" * 70)
    print("Collecting data...")
    print("=" * 70)
    
    successful = 0
    failed = 0
    
    for i, date in enumerate(missed_dates, 1):
        print(f"\n[{i}/{len(missed_dates)}] Processing {date}...")
        
        success = collect_data_for_date(
            date,
            save_raw=not args.skip_raw,
            save_processed=not args.skip_processed,
            save_csv=not args.skip_csv
        )
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Add delay to respect API rate limits
        if i < len(missed_dates) and args.delay > 0:
            time.sleep(args.delay)
    
    # Summary
    print("\n" + "=" * 70)
    print("Collection Complete!")
    print("=" * 70)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(missed_dates)}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

