#!/usr/bin/env python3
"""
View Data Script

Display AUD tracking data in various formats.
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.currency_storage import load_data, load_latest_data
from src.currency_formatter import (
    standardize_data,
    format_table,
    format_summary,
    format_json,
    format_csv,
    format_custom
)


def list_available_dates(data_dir: str = "data/forex_data/processed") -> list:
    """List all available dates with data files."""
    if not os.path.exists(data_dir):
        return []
    
    files = sorted(Path(data_dir).glob("aud_daily_*.json"), reverse=True)
    dates = []
    for file in files:
        # Extract date from filename: aud_daily_YYYY-MM-DD.json
        date_str = file.stem.replace("aud_daily_", "")
        dates.append((date_str, str(file)))
    
    return dates


def main():
    parser = argparse.ArgumentParser(
        description="View AUD Daily Tracker data in various formats"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to view (YYYY-MM-DD). Defaults to latest.",
        default=None
    )
    parser.add_argument(
        "--format",
        choices=["table", "summary", "json", "csv", "minimal", "detailed"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to specific JSON file to view",
        default=None
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available dates"
    )
    
    args = parser.parse_args()
    
    # List available dates
    if args.list:
        dates = list_available_dates()
        if dates:
            print("\nAvailable dates:")
            print("-" * 50)
            for date_str, filepath in dates:
                print(f"  {date_str} - {filepath}")
            print()
        else:
            print("No data files found in data/forex_data/processed/")
        return
    
    # Load data
    data = None
    
    if args.file:
        # Load from specific file
        data = load_data(args.file)
        if not data:
            print(f"Error: Could not load file {args.file}")
            return
    elif args.date:
        # Load from specific date - validate date format to prevent path traversal
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', args.date):
            print(f"Error: Invalid date format. Expected YYYY-MM-DD, got: {args.date}")
            return
        filepath = os.path.join("data/forex_data/processed", f"aud_daily_{args.date}.json")
        data = load_data(filepath)
        if not data:
            print(f"Error: No data found for date {args.date}")
            print("Use --list to see available dates")
            return
    else:
        # Load latest
        data = load_latest_data()
        if not data:
            print("Error: No data files found")
            print("Run: python scripts/daily_update.py to collect data first")
            return
    
    # Standardize data
    standardized_data = standardize_data(data)
    
    # Format and display
    if args.format == "table":
        print(format_table(standardized_data))
    elif args.format == "summary":
        print(format_summary(standardized_data))
    elif args.format == "json":
        print(format_json(standardized_data))
    elif args.format == "csv":
        print(format_csv(standardized_data))
    elif args.format == "minimal":
        print(format_custom(standardized_data, "minimal"))
    elif args.format == "detailed":
        print(format_custom(standardized_data, "detailed"))


if __name__ == "__main__":
    main()

