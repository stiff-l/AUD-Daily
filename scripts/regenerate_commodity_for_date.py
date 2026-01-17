#!/usr/bin/env python3
"""
Regenerate commodity HTML and JPEG for a specific date using CSV data.

Usage: python scripts/regenerate_commodity_for_date.py YYYY-MM-DD
"""

import sys
import os
from datetime import datetime
import pandas as pd

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.commodity_history import load_commodity_history_csv
from src.commodity_formatter import standardize_commodity_data
from scripts.generate_mineral_commodities_html import generate_mineral_commodities_html


def csv_row_to_standardized_data(row, date_str):
    """
    Convert a CSV row to standardized commodity data format.
    
    Args:
        row: pandas Series with commodity price columns
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Standardized data dictionary
    """
    commodities = {}
    
    # Map CSV columns to commodity symbols
    commodity_mapping = {
        'gold_price': 'GOLD',
        'silver_price': 'SILVER',
        'copper_price': 'COPPER',
        'aluminium_price': 'ALUMINIUM',
        'nickel_price': 'NICKEL'
    }
    
    for csv_col, symbol in commodity_mapping.items():
        price = row.get(csv_col)
        if pd.notna(price):
            commodities[symbol] = {
                "price_aud": float(price),
                "price_usd": None,  # Not in CSV
                "unit": "oz" if symbol in ["GOLD", "SILVER"] else "tonne",
                "currency": "AUD",
                "date": date_str,
                "source": "csv"
            }
    
    # Create standardized data structure
    data = {
        "date": date_str,
        "timestamp": row.get('timestamp', datetime.now().isoformat()),
        "commodities": commodities
    }
    
    return standardize_commodity_data(data)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/regenerate_commodity_for_date.py YYYY-MM-DD")
        sys.exit(1)
    
    date_str = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format. Use YYYY-MM-DD (e.g., 2026-01-15)")
        sys.exit(1)
    
    print(f"Loading CSV data for {date_str}...")
    
    # Load CSV
    csv_path = "data/commodities_data/processed/commodity_daily.csv"
    if not os.path.exists(csv_path):
        # Try relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, '..', csv_path)
        csv_path = os.path.abspath(csv_path)
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    df = load_commodity_history_csv(csv_path)
    
    if df is None or df.empty:
        print(f"Error: CSV file is empty or could not be loaded")
        sys.exit(1)
    
    # Find row for the specified date
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    row = df[df['date'] == date_obj]
    
    if row.empty:
        print(f"Error: No data found for date {date_str}")
        print(f"Available dates in CSV: {sorted(df['date'].dt.strftime('%Y-%m-%d').unique().tolist())}")
        sys.exit(1)
    
    # Get the first matching row (should be only one after deduplication)
    row_data = row.iloc[0]
    
    print(f"Found data for {date_str}:")
    print(f"  Gold: {row_data.get('gold_price', 'N/A')}")
    print(f"  Silver: {row_data.get('silver_price', 'N/A')}")
    print(f"  Copper: {row_data.get('copper_price', 'N/A')}")
    print(f"  Aluminium: {row_data.get('aluminium_price', 'N/A')}")
    print(f"  Nickel: {row_data.get('nickel_price', 'N/A')}")
    
    # Convert to standardized format
    standardized_data = csv_row_to_standardized_data(row_data, date_str)
    
    # Generate HTML and JPEG
    template_path = "templates/commodities_m_template.html"
    if not os.path.exists(template_path):
        # Try relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, '..', template_path)
        template_path = os.path.abspath(template_path)
    
    if not os.path.exists(template_path):
        print(f"Error: Template file not found at {template_path}")
        sys.exit(1)
    
    print(f"\nGenerating HTML and JPEG...")
    html_path, jpeg_path = generate_mineral_commodities_html(
        template_path,
        "data/commodities_data",
        standardized_data
    )
    
    print(f"\n✓ Successfully generated HTML: {html_path}")
    if jpeg_path:
        print(f"✓ Successfully generated JPEG: {jpeg_path}")
    else:
        print(f"⚠ JPEG generation failed (HTML was still created)")


if __name__ == "__main__":
    main()
