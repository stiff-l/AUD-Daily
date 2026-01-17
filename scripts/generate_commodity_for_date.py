#!/usr/bin/env python3
"""
Generate Commodity data for a specific date or date range using Metals.Dev API

Fetches commodity prices and saves them with the specified date(s).
Updates: raw JSON, processed JSON, CSV, HTML, and JPEG.

Usage:
    # Single date
    python scripts/generate_commodity_for_date.py 2026-01-14
    
    # Date range (more efficient - uses timeseries API)
    python scripts/generate_commodity_for_date.py 2026-01-01 2026-01-16
    
    # Date range from start date to today
    python scripts/generate_commodity_for_date.py 2026-01-01
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.commodity_collector import (
    collect_all_commodity_data,
    fetch_metals_dev_timeseries,
    extract_timeseries_commodity_prices,
    fetch_base_metals_yfinance
)
from src.commodity_storage import load_commodity_data
from src.commodity_storage import save_raw_commodity_data, save_daily_commodity_data, save_to_commodity_table
from src.commodity_formatter import standardize_commodity_data
from scripts.generate_mineral_commodities_html import generate_mineral_commodities_html
from scripts.cleanup_raw_files import cleanup_raw_files


def process_single_date(date_str: str, use_timeseries: bool = False, timeseries_data: dict = None, fill_missing_base_metals: bool = True):
    """
    Process and save data for a single date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        use_timeseries: If True, extract from timeseries_data instead of fetching current data
        timeseries_data: Pre-fetched timeseries API response (required if use_timeseries=True)
        fill_missing_base_metals: If True, use yfinance to fill missing copper/aluminium/nickel prices
    """
    print(f"\n{'=' * 60}")
    print(f"Processing date: {date_str}")
    print(f"{'=' * 60}")
    
    try:
        # Try to load existing data first
        existing_data_path = os.path.join("data", "commodities_data", "processed", f"commodity_daily_{date_str}.json")
        existing_data = None
        if os.path.exists(existing_data_path):
            try:
                existing_data = load_commodity_data(existing_data_path)
                print(f"Found existing data for {date_str}, will merge with new data")
            except Exception as e:
                print(f"Warning: Could not load existing data: {e}")
        
        if use_timeseries and timeseries_data:
            # Extract data for this date from timeseries response
            print(f"Extracting data for {date_str} from timeseries response...")
            commodities_data = extract_timeseries_commodity_prices(timeseries_data, date_str)
            
            # Build data structure compatible with standardize_commodity_data
            data = {
                "collection_date": datetime.now().isoformat(),
                "commodities": commodities_data
            }
        else:
            # Collect commodity data (fetches current prices from API)
            print("Fetching current commodity prices from Metals.Dev API...")
            data = collect_all_commodity_data()
            
            # Override the date in the collected data
            if "commodities" in data and isinstance(data["commodities"], dict):
                if "commodities" in data["commodities"]:
                    # Nested structure
                    for commodity in data["commodities"]["commodities"].values():
                        if isinstance(commodity, dict):
                            commodity["date"] = date_str
                else:
                    # Direct structure
                    for commodity in data["commodities"].values():
                        if isinstance(commodity, dict):
                            commodity["date"] = date_str
        
        # Standardize data (this will also set the date)
        standardized_data = standardize_commodity_data(data)
        # Override the date to ensure it's the requested date
        standardized_data['date'] = date_str
        
        # Update commodity dates to match
        for commodity in standardized_data.get('commodities', {}).values():
            if isinstance(commodity, dict):
                commodity['date'] = date_str
        
        # Fill missing base metals with yfinance if requested
        if fill_missing_base_metals:
            print("Checking for missing base metals (Copper, Aluminium, Nickel)...")
            base_metals_needed = ["COPPER", "ALUMINIUM", "NICKEL"]
            missing_metals = []
            
            for metal in base_metals_needed:
                metal_data = standardized_data.get('commodities', {}).get(metal, {})
                if not metal_data or metal_data.get('price_aud') is None:
                    missing_metals.append(metal)
            
            if missing_metals:
                print(f"Fetching missing base metals from yfinance: {', '.join(missing_metals)}")
                yfinance_data = fetch_base_metals_yfinance(date_str)
                
                # Merge yfinance data into standardized data
                for metal, metal_data in yfinance_data.items():
                    if metal in missing_metals and metal_data.get('price_aud') is not None:
                        standardized_data['commodities'][metal] = metal_data
                        print(f"  ✓ Filled {metal} from yfinance")
        
        # Merge with existing data if available (preserve existing data for metals not in new data)
        if existing_data:
            existing_commodities = existing_data.get('commodities', {})
            for metal, metal_data in existing_commodities.items():
                # Only preserve if new data doesn't have it or it's None
                if metal not in standardized_data.get('commodities', {}) or \
                   standardized_data['commodities'][metal].get('price_aud') is None:
                    if metal_data.get('price_aud') is not None:
                        standardized_data['commodities'][metal] = metal_data
                        print(f"  Preserved existing {metal} data")
        
        # Check if we got any data
        if not standardized_data.get('commodities'):
            print(f"Warning: No commodity data collected for {date_str}")
            return False
        
        # Check if we have valid prices
        has_valid_prices = any(
            comm.get('price_aud') is not None 
            for comm in standardized_data.get('commodities', {}).values()
        )
        
        if not has_valid_prices:
            print(f"Warning: No valid prices found for {date_str} - skipping")
            return False
        
        print(f"Data collected for commodities: {list(standardized_data.get('commodities', {}).keys())}")
        
        # Save raw data (with timestamp) - only for single date mode or first date in range
        if not use_timeseries:
            print("Saving raw data...")
            save_raw_commodity_data(data, output_dir="data/commodities_data/raw")
        
        # Save daily data (date-based filename, overwrites if exists)
        print("Saving daily data...")
        save_daily_commodity_data(standardized_data, output_dir="data/commodities_data/processed")
        
        # Save to commodity history table (CSV)
        print("Saving to commodity history table...")
        save_to_commodity_table(standardized_data)
        
        # Generate mineral commodities HTML and JPEG
        print("Generating HTML and JPEG...")
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'commodities_m_template.html')
        if not os.path.exists(template_path):
            template_path = "templates/commodities_m_template.html"
        
        if os.path.exists(template_path):
            html_path, jpeg_path = generate_mineral_commodities_html(
                template_path,
                output_dir="data/commodities_data",
                standardized_data=standardized_data
            )
            print(f"✓ Successfully generated HTML: {html_path}")
            if jpeg_path:
                print(f"✓ Successfully generated JPEG: {jpeg_path}")
            else:
                print(f"⚠ JPEG generation failed (HTML was still created)")
        else:
            print(f"Warning: Template not found at {template_path}, skipping HTML generation.")
        
        print(f"✓ Data collection complete for {date_str}!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error processing date {date_str}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single date: python scripts/generate_commodity_for_date.py YYYY-MM-DD")
        print("  Date range:  python scripts/generate_commodity_for_date.py START_DATE END_DATE")
        print("  Range to today: python scripts/generate_commodity_for_date.py START_DATE")
        print("\nExample:")
        print("  python scripts/generate_commodity_for_date.py 2026-01-14")
        print("  python scripts/generate_commodity_for_date.py 2026-01-01 2026-01-16")
        sys.exit(1)
    
    start_date_str = sys.argv[1]
    
    # Validate start date format
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format. Use YYYY-MM-DD (e.g., 2026-01-14)")
        sys.exit(1)
    
    # Determine end date
    if len(sys.argv) >= 3:
        end_date_str = sys.argv[2]
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid end date format. Use YYYY-MM-DD (e.g., 2026-01-16)")
            sys.exit(1)
    else:
        # Default to today if only start date provided
        end_date = datetime.now()
        end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Validate date range
    if start_date > end_date:
        print(f"Error: Start date ({start_date_str}) must be before or equal to end date ({end_date_str})")
        sys.exit(1)
    
    # Check if it's a single date or range
    is_range = start_date_str != end_date_str
    
    print("=" * 60)
    if is_range:
        print("AUD Daily Tracker - Commodity Data Collection (Date Range)")
        print(f"Date Range: {start_date_str} to {end_date_str}")
        print(f"Using timeseries API for efficient bulk collection")
    else:
        print("AUD Daily Tracker - Commodity Data Collection (Single Date)")
        print(f"Target Date: {start_date_str}")
    print("=" * 60)
    print()
    
    try:
        if is_range:
            # Use timeseries API for date range (more efficient)
            print(f"Fetching commodity prices for date range using timeseries API...")
            timeseries_data = fetch_metals_dev_timeseries(start_date_str, end_date_str)
            
            if not timeseries_data:
                print("Error: Failed to fetch timeseries data from API")
                sys.exit(1)
            
            rates = timeseries_data.get("rates", {})
            if not rates:
                print("Warning: No rates found in API response")
                sys.exit(1)
            
            print(f"✓ Successfully fetched data for {len(rates)} date(s)")
            
            # Save raw timeseries data once
            print("Saving raw timeseries data...")
            raw_data = {
                "collection_date": datetime.now().isoformat(),
                "timeseries_response": timeseries_data,
                "date_range": {
                    "start": start_date_str,
                    "end": end_date_str
                }
            }
            save_raw_commodity_data(raw_data, output_dir="data/commodities_data/raw")
            print()
            
            # Process each date in the range
            dates_to_process = sorted(rates.keys())
            successful = 0
            failed = 0
            
            for date_str in dates_to_process:
                success = process_single_date(date_str, use_timeseries=True, timeseries_data=timeseries_data, fill_missing_base_metals=True)
                if success:
                    successful += 1
                else:
                    failed += 1
            
            # Cleanup raw files after processing all dates
            try:
                print("\nCleaning up old raw files...")
                cleanup_raw_files(verbose=False)
            except Exception as e:
                print(f"Warning: Error during cleanup: {e}")
            
            print("\n" + "=" * 60)
            print(f"✓ Bulk data collection complete!")
            print(f"  Successfully processed: {successful} date(s)")
            if failed > 0:
                print(f"  Failed: {failed} date(s)")
            print("=" * 60)
        else:
            # Single date mode (backward compatible)
            success = process_single_date(start_date_str, use_timeseries=False)
            
            # Cleanup raw files
            try:
                print("\nCleaning up old raw files...")
                cleanup_raw_files(verbose=False)
            except Exception as e:
                print(f"Warning: Error during cleanup: {e}")
            
            if success:
                print("\n" + "=" * 60)
                print(f"✓ Data collection complete for {start_date_str}!")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print(f"❌ Data collection failed for {start_date_str}")
                print("=" * 60)
                sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error during data collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
