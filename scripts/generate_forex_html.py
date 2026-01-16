#!/usr/bin/env python3
"""
Generate Forex HTML from Template

This script reads an HTML template with placeholders and replaces them with
daily forex data, then saves the result to data/forex_data/HTML/ and also
converts it to JPEG format saved to data/forex_data/JPEG/.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.currency_collector import fetch_currency_rates
from src.currency_formatter import standardize_data
from src.currency_history import load_currency_history_csv
from src.currency_storage import save_raw_data, save_daily_data, save_to_currency_table
import pandas as pd

# Import HTML utilities
try:
    from .html_utils import (
        generate_arrow_html as generate_arrow_html_base,
        html_to_jpeg,
        PLAYWRIGHT_AVAILABLE,
        SELENIUM_AVAILABLE
    )
except ImportError:
    try:
        from html_utils import (
            generate_arrow_html as generate_arrow_html_base,
            html_to_jpeg,
            PLAYWRIGHT_AVAILABLE,
            SELENIUM_AVAILABLE
        )
    except ImportError:
        from scripts.html_utils import (
            generate_arrow_html as generate_arrow_html_base,
            html_to_jpeg,
            PLAYWRIGHT_AVAILABLE,
            SELENIUM_AVAILABLE
        )


def fetch_all_currency_rates():
    """
    Fetch all required currency rates (USD, EUR, CNY, SGD, JPY).
    
    Returns:
        Dictionary with currency rates
    """
    # fetch_currency_rates already includes JPY
    return fetch_currency_rates()


def format_rate(rate, decimals=4):
    """
    Format exchange rate with specified decimal places.
    
    Args:
        rate: The exchange rate value
        decimals: Number of decimal places (default: 4)
        
    Returns:
        Formatted rate string
    """
    if rate is None:
        return "N/A"
    return f"{rate:.{decimals}f}"


def get_previous_day_rates(current_date_str, csv_path="data/forex_data/processed/currency_daily.csv"):
    """
    Get currency rates for the previous day (n-1).
    
    Args:
        current_date_str: Current date in YYYY-MM-DD format
        csv_path: Path to the currency history CSV file
        
    Returns:
        Dictionary with currency codes as keys and rates as values, or None if not found
    """
    try:
        # Try relative path first, then absolute path
        if not os.path.exists(csv_path):
            # Try relative to script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(script_dir, '..', csv_path)
            if os.path.exists(alt_path):
                csv_path = os.path.abspath(alt_path)
            else:
                return None
        
        df = load_currency_history_csv(csv_path)
        
        if df is None or df.empty:
            return None
        
        # Parse current date
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        
        # Find previous day (go back up to 7 days to find the most recent data)
        previous_rates = None
        for days_back in range(1, 8):
            check_date = current_date - timedelta(days=days_back)
            previous_row = df[df['date'] == check_date]
            
            if not previous_row.empty:
                row = previous_row.iloc[0]
                previous_rates = {
                    "USD": row.get('usd_rate') if pd.notna(row.get('usd_rate')) else None,
                    "EUR": row.get('eur_rate') if pd.notna(row.get('eur_rate')) else None,
                    "JPY": row.get('jpy_rate') if pd.notna(row.get('jpy_rate')) else None,
                    "CNY": row.get('cny_rate') if pd.notna(row.get('cny_rate')) else None,
                    "SGD": row.get('sgd_rate') if pd.notna(row.get('sgd_rate')) else None,
                }
                # Verify we got at least one valid rate
                if any(v is not None for v in previous_rates.values()):
                    return previous_rates
        
        return None
    except Exception as e:
        print(f"Warning: Could not load previous day's rates: {e}")
        return None


def generate_arrow_html(current_rate, previous_rate):
    """
    Generate arrow HTML based on rate comparison.
    
    Args:
        current_rate: Current day's rate
        previous_rate: Previous day's rate
        
    Returns:
        HTML string for the arrow icon, or empty string if no comparison possible
    """
    return generate_arrow_html_base(current_rate, previous_rate, arrow_class="currency-arrow")


def replace_html_placeholders(html_content, data, include_arrows=False):
    """
    Replace placeholders in HTML content with actual data.
    
    Args:
        html_content: The HTML template content as string
        data: Standardized data dictionary with currencies
        include_arrows: Whether to include arrow placeholders (for arrow template)
        
    Returns:
        HTML content with placeholders replaced
    """
    # Preserve the date from input data if it exists (for historical dates)
    preserved_date = data.get("date") if isinstance(data, dict) else None
    
    # Standardize data if needed
    standardized = standardize_data(data)
    
    # Use preserved date if available, otherwise use standardized date, otherwise today
    date_str = preserved_date or standardized.get("date") or datetime.now().strftime("%Y-%m-%d")
    # Ensure standardized data uses the correct date
    standardized["date"] = date_str
    
    full_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    
    # Get currency rates
    currencies = standardized.get("currencies", {})
    rates = {
        "USD": currencies.get("USD", {}).get("rate") if currencies.get("USD") else None,
        "EUR": currencies.get("EUR", {}).get("rate") if currencies.get("EUR") else None,
        "JPY": currencies.get("JPY", {}).get("rate") if currencies.get("JPY") else None,
        "CNY": currencies.get("CNY", {}).get("rate") if currencies.get("CNY") else None,
        "SGD": currencies.get("SGD", {}).get("rate") if currencies.get("SGD") else None,
    }
    
    # Get previous day's rates if arrows are needed
    previous_rates = None
    if include_arrows:
        previous_rates = get_previous_day_rates(date_str)
        if previous_rates:
            print(f"  Found previous day's rates for comparison")
        else:
            print(f"  Warning: No previous day's rates found - arrows will not be displayed")
    
    # Build replacement dictionary
    replacements = {
        "{{FULL_DATE}}": full_date,
        "{FULL_DATE}": full_date,
    }
    
    for currency in ["USD", "EUR", "JPY", "CNY", "SGD"]:
        rate_value = format_rate(rates[currency], decimals=3)
        replacements["{{" + currency + "_RATE}}"] = rate_value
        replacements["{" + currency + "_RATE}"] = rate_value
        
        # Add arrow if needed
        if include_arrows:
            arrow_html = ""
            if previous_rates and previous_rates.get(currency) is not None:
                arrow_html = generate_arrow_html(rates[currency], previous_rates.get(currency))
                if arrow_html:
                    direction = "up" if rates[currency] and previous_rates.get(currency) and float(rates[currency]) > float(previous_rates.get(currency)) else "down"
                    print(f"  {currency}: {rate_value} ({direction} from previous day)")
            else:
                print(f"  {currency}: {rate_value} (no previous data for comparison)")
            replacements["{{" + currency + "_ARROW}}"] = arrow_html
            replacements["{" + currency + "_ARROW}"] = arrow_html
    
    # Replace all placeholders
    result = html_content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    
    return result


# html_to_jpeg is imported from html_utils


def generate_forex_html(template_path, output_dir="data/forex_data", standardized_data=None):
    """
    Generate HTML file from template with daily forex data.
    Also saves a JPEG version of the HTML.
    
    Args:
        template_path: Path to the HTML template file
        output_dir: Base directory to save the generated files (will create HTML/ and JPEG/ subdirectories)
        standardized_data: Optional pre-standardized data dictionary. If None, fetches fresh data.
        
    Returns:
        Tuple of (path to HTML file, path to JPEG file) or (path to HTML file, None) if JPEG conversion failed
    """
    # Check if template exists
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    # Read template
    print(f"Reading template: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Use provided data or fetch fresh data
    raw_data = None
    if standardized_data is None:
        print("Fetching daily forex rates...")
        data = fetch_all_currency_rates()
        raw_data = {
            "collection_date": datetime.now().isoformat(),
            "currencies": data
        }
        
        # Standardize data
        standardized_data = standardize_data(raw_data)
    else:
        print("Using provided forex data...")
        # If standardized_data is provided, we still need raw_data for saving
        # Create a raw_data structure from standardized_data
        raw_data = {
            "collection_date": standardized_data.get("timestamp", datetime.now().isoformat()),
            "currencies": {
                "timestamp": standardized_data.get("timestamp", datetime.now().isoformat()),
                "currencies": standardized_data.get("currencies", {})
            }
        }
    
    # Save raw and processed data, and update CSVs
    try:
        print("\nSaving data files...")
        # Determine base directory for data storage
        # If output_dir is "data/forex_data", use it directly; otherwise construct path
        if "forex_data" in output_dir:
            base_data_dir = output_dir
        else:
            base_data_dir = "data/forex_data"
        
        # Save raw data (with timestamp)
        if raw_data:
            raw_output_dir = os.path.join(base_data_dir, "raw")
            save_raw_data(raw_data, output_dir=raw_output_dir)
        
        # Save daily data (date-based filename, overwrites if exists)
        processed_output_dir = os.path.join(base_data_dir, "processed")
        save_daily_data(standardized_data, output_dir=processed_output_dir)
        
        # Save to currency history table (CSV)
        save_to_currency_table(standardized_data)
        print("✓ Data files saved successfully")
    except Exception as e:
        print(f"⚠ Warning: Error saving data files: {e}")
        # Don't fail HTML generation if data saving fails
        import traceback
        traceback.print_exc()
    
    # Check if template has arrow placeholders by looking for ARROW placeholders in the content
    is_arrow_template = any(f"{{{{{currency}_ARROW}}}}" in template_content or 
                            f"{{{currency}_ARROW}}" in template_content
                            for currency in ["USD", "EUR", "JPY", "CNY", "SGD"])
    
    if is_arrow_template:
        print("Arrow placeholders detected in template - will include arrows based on previous day's rates")
    
    # Replace placeholders
    print("Replacing placeholders...")
    html_content = replace_html_placeholders(template_content, standardized_data, include_arrows=is_arrow_template)
    
    # Create output subdirectories
    html_dir = os.path.join(output_dir, "HTML")
    jpeg_dir = os.path.join(output_dir, "JPEG")
    Path(html_dir).mkdir(parents=True, exist_ok=True)
    Path(jpeg_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename with date
    date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
    output_filename = f"forex_{date_str}.html"
    html_path = os.path.join(html_dir, output_filename)
    jpeg_filename = f"forex_{date_str}.jpg"
    jpeg_path = os.path.join(jpeg_dir, jpeg_filename)
    
    # Save generated HTML
    print(f"Saving HTML to: {html_path}")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML generated successfully: {html_path}")
    
    # Convert HTML to JPEG
    print(f"Converting HTML to JPEG...")
    jpeg_result = html_to_jpeg(html_path, jpeg_path)
    
    return (html_path, jpeg_result)


def generate_forex_from_api(template_path=None, output_dir="data/forex_data", standardized_data=None):
    """
    Generate HTML file from template when data is fetched from API.
    This is a convenience function that uses HTML template for API-fetched data.
    
    Args:
        template_path: Path to the HTML template file (default: templates/forex_template.html)
        output_dir: Directory to save the generated HTML
        standardized_data: Optional pre-standardized data dictionary. If None, fetches fresh data.
        
    Returns:
        Tuple of (path to HTML file, path to JPEG file) or (path to HTML file, None) if JPEG conversion failed
    """
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'forex_template.html')
    
    return generate_forex_html(template_path, output_dir, standardized_data)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate HTML from template with daily forex data"
    )
    parser.add_argument(
        "template",
        nargs="?",
        help="Path to HTML template file (default: templates/forex_template.html)"
    )
    parser.add_argument(
        "-o", "--output",
        default="data/forex_data",
        help="Output directory (default: data/forex_data)"
    )
    
    args = parser.parse_args()
    
    # Default template path if not provided
    template_path = args.template
    if not template_path:
        possible_paths = [
            "templates/forex_template.html",
            "forex_template.html",
            "template.html"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            print("Error: No template file specified and no default template found.")
            print("Please provide the template path as an argument or place it at:")
            print("  - templates/forex_template.html")
            print("  - forex_template.html")
            sys.exit(1)
    
    try:
        generate_forex_html(template_path, args.output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
