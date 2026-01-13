#!/usr/bin/env python3
"""
Generate Forex HTML from Template

This script reads an HTML template with placeholders and replaces them with
daily forex data, then saves the result to data/forex_data/.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import fetch_currency_rates
from src.data_formatter import standardize_data


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


def replace_html_placeholders(html_content, data):
    """
    Replace placeholders in HTML content with actual data.
    
    Args:
        html_content: The HTML template content as string
        data: Standardized data dictionary with currencies
        
    Returns:
        HTML content with placeholders replaced
    """
    # Standardize data if needed
    standardized = standardize_data(data)
    
    # Get date
    date_str = standardized.get("date") or datetime.now().strftime("%Y-%m-%d")
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
    
    # Build replacement dictionary
    replacements = {
        "{{FULL_DATE}}": full_date,
        "{FULL_DATE}": full_date,
    }
    
    for currency in ["USD", "EUR", "JPY", "CNY", "SGD"]:
        rate_value = format_rate(rates[currency], decimals=3)
        replacements["{{" + currency + "_RATE}}"] = rate_value
        replacements["{" + currency + "_RATE}"] = rate_value
    
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
    
    # Replace placeholders
    print("Replacing placeholders...")
    html_content = replace_html_placeholders(template_content, standardized_data)
    
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
