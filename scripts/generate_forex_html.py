#!/usr/bin/env python3
"""
Generate Forex HTML from Template

This script reads an HTML template with placeholders and replaces them with
daily forex data, then saves the result to data/forex_data/.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import fetch_currency_rates
from src.data_formatter import standardize_data
from src.currency_history import load_currency_history_csv
import pandas as pd


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


def get_previous_day_rates(current_date_str, csv_path="data/processed/currency_daily.csv"):
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
    if current_rate is None or previous_rate is None:
        return ""
    
    try:
        current = float(current_rate)
        previous = float(previous_rate)
        
        if current > previous:
            # Price is up - green up arrow
            return '<div class="currency-arrow arrow-up"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7 14L12 9L17 14H7Z" fill="currentColor"/></svg></div>'
        elif current < previous:
            # Price is down - red down arrow
            return '<div class="currency-arrow arrow-down"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7 10L12 15L17 10H7Z" fill="currentColor"/></svg></div>'
        else:
            # No change - white dash
            return '<div class="currency-arrow arrow-neutral"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><line x1="7" y1="12" x2="17" y2="12" stroke="currentColor" stroke-width="3"/></svg></div>'
    except (ValueError, TypeError):
        return ""


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


def generate_forex_html(template_path, output_dir="data/forex_data", standardized_data=None):
    """
    Generate HTML file from template with daily forex data.
    
    Args:
        template_path: Path to the HTML template file
        output_dir: Directory to save the generated HTML
        standardized_data: Optional pre-standardized data dictionary. If None, fetches fresh data.
        
    Returns:
        Path to the generated HTML file
    """
    # Check if template exists
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    # Read template
    print(f"Reading template: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Use provided data or fetch fresh data
    if standardized_data is None:
        print("Fetching daily forex rates...")
        data = fetch_all_currency_rates()
        
        # Standardize data
        standardized_data = standardize_data({
            "collection_date": datetime.now().isoformat(),
            "currencies": data
        })
    else:
        print("Using provided forex data...")
    
    # Check if template has arrow placeholders by looking for ARROW placeholders in the content
    is_arrow_template = any(f"{{{{{currency}_ARROW}}}}" in template_content or 
                            f"{{{currency}_ARROW}}" in template_content
                            for currency in ["USD", "EUR", "JPY", "CNY", "SGD"])
    
    if is_arrow_template:
        print("Arrow placeholders detected in template - will include arrows based on previous day's rates")
    
    # Replace placeholders
    print("Replacing placeholders...")
    html_content = replace_html_placeholders(template_content, standardized_data, include_arrows=is_arrow_template)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename with date
    date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
    output_filename = f"forex_{date_str}.html"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save generated HTML
    print(f"Saving to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML generated successfully: {output_path}")
    return output_path


def generate_forex_from_api(template_path=None, output_dir="data/forex_data", standardized_data=None):
    """
    Generate HTML file from template when data is fetched from API.
    This is a convenience function that uses HTML template for API-fetched data.
    
    Args:
        template_path: Path to the HTML template file (default: templates/forex_template.html)
        output_dir: Directory to save the generated HTML
        standardized_data: Optional pre-standardized data dictionary. If None, fetches fresh data.
        
    Returns:
        Path to the generated HTML file
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
