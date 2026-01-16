#!/usr/bin/env python3
"""
Generate Forex HTML for a specific date

Usage:
    python scripts/generate_forex_for_date.py 2025-12-30
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.generate_forex_html import generate_forex_html
from src.currency_collector import collect_historical_data_for_date
from src.currency_formatter import standardize_data
from src.rba_historical_importer import RBAForexImporter


def get_data_from_rba(date_str):
    """Try to get currency data from RBA database"""
    importer = RBAForexImporter()
    currencies_data = {
        "timestamp": datetime.now().isoformat(),
        "currencies": {}
    }
    
    currencies_to_fetch = ["USD", "EUR", "CNY", "SGD", "JPY"]
    found_any = False
    
    for currency in currencies_to_fetch:
        rate = importer.query_rate(date_str, currency, "AUD")
        if rate:
            currencies_data["currencies"][currency] = {
                "rate": rate,
                "base": "AUD",
                "date": date_str
            }
            found_any = True
    
    if found_any:
        return {
            "collection_date": datetime.now().isoformat(),
            "currencies": currencies_data
        }
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_forex_for_date.py YYYY-MM-DD")
        sys.exit(1)
    
    date_str = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-30)")
        sys.exit(1)
    
    print(f'Fetching historical data for {date_str}...')
    
    # Try RBA database first
    historical_data = get_data_from_rba(date_str)
    
    # If RBA doesn't have it, try API
    if not historical_data or not historical_data.get('currencies', {}).get('currencies'):
        print("RBA database doesn't have data, trying API...")
        historical_data = collect_historical_data_for_date(date_str)
    
    # Standardize the data and ensure the date is set correctly
    standardized = standardize_data(historical_data)
    # Override the date to ensure it's the requested date
    standardized['date'] = date_str
    
    # Update currency dates to match
    for currency in standardized.get('currencies', {}).values():
        currency['date'] = date_str
    
    # Check if we got any data
    if not standardized.get('currencies'):
        print(f"Warning: No currency data found for {date_str}")
        print("This might be because:")
        print("  - The date is in the future")
        print("  - The date is a weekend/holiday")
        print("  - The API doesn't have data for this date")
        sys.exit(1)
    
    print(f'Data collected for currencies: {list(standardized.get("currencies", {}).keys())}')
    
    # Generate the output - always use HTML template
    template_path = 'templates/forex_template.html'
    html_path, jpeg_path = generate_forex_html(template_path, 'data/forex_data', standardized)
    print(f'✓ Successfully generated HTML: {html_path}')
    if jpeg_path:
        print(f'✓ Successfully generated JPEG: {jpeg_path}')


if __name__ == "__main__":
    main()

