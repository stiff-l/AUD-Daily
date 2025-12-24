#!/usr/bin/env python3
"""
Generate Forex SVG from Template

This script reads an SVG template with placeholders and replaces them with
daily forex data, then saves the result to data/forex_data/.
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import re

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_collector import fetch_currency_rates
from src.data_formatter import standardize_data


def fetch_all_currency_rates():
    """
    Fetch all required currency rates including JPY.
    
    Returns:
        Dictionary with currency rates
    """
    # Fetch standard rates (USD, EUR, CNY, SGD)
    data = fetch_currency_rates()
    
    # Add JPY if not already included
    if "JPY" not in data.get("currencies", {}):
        try:
            import requests
            response = requests.get("https://api.exchangerate-api.com/v4/latest/AUD", timeout=10)
            response.raise_for_status()
            rates = response.json()
            
            if "JPY" in rates.get("rates", {}):
                data["currencies"]["JPY"] = {
                    "rate": rates["rates"]["JPY"],
                    "base": "AUD",
                    "date": rates.get("date", datetime.now().strftime("%Y-%m-%d"))
                }
        except Exception as e:
            print(f"Warning: Could not fetch JPY rate: {e}")
    
    return data


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


def extract_text_from_element(element_content):
    """
    Extract all text content from a text element, including from tspan children.
    
    Args:
        element_content: The content of a text element (including tspan tags)
        
    Returns:
        The full text content as a single string
    """
    # Remove all XML tags and extract text
    # This regex matches <tspan...>content</tspan> and extracts the content
    text = element_content
    
    # First, extract text from tspan elements
    tspan_pattern = r'<tspan[^>]*>(.*?)</tspan>'
    tspan_matches = re.findall(tspan_pattern, text, re.DOTALL)
    
    # Replace tspan elements with their content
    text = re.sub(tspan_pattern, r'\1', text, flags=re.DOTALL)
    
    # Remove any remaining XML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    return text


def replace_svg_placeholders(svg_content, data):
    """
    Replace placeholders in SVG content with actual data.
    
    This function handles text elements that may be split across <tspan> elements,
    which is common when exporting from design software.
    
    BEST SVG TEMPLATE FORMAT FOR ACCURATE REPLACEMENT:
    - Use <text> elements (NOT converted to paths) for placeholders
    - Use consistent placeholder format: {{PLACEHOLDER}} (double braces)
    - Keep SVG readable (not minified) for easier debugging
    - Place placeholders in text content, not in path data
    
    Supported placeholder formats:
    - {{PLACEHOLDER}} (recommended - double braces)
    - {PLACEHOLDER} (single braces)
    - {PLACEHOLDER}} (malformed with extra closing brace - handled for compatibility)
    
    Available placeholders:
    - {{FULL_DATE}} or {FULL_DATE} - Full date (e.g., "December 24, 2025")
    - {{USD_RATE}} or {{USD_RATES}} or {USD_RATE} or {USD_RATES} - USD exchange rate
    - {{EUR_RATE}} or {{EUR_RATES}} or {EUR_RATE} or {EUR_RATES} - EUR exchange rate
    - {{JPY_RATE}} or {{JPY_RATES}} or {JPY_RATE} or {JPY_RATES} - JPY exchange rate
    - {{CNY_RATE}} or {{CNY_RATES}} or {CNY_RATE} or {CNY_RATES} - CNY exchange rate
    - {{SGD_RATE}} or {{SGD_RATES}} or {SGD_RATE} or {SGD_RATES} - SGD exchange rate
    
    Args:
        svg_content: The SVG template content as string
        data: Standardized data dictionary with currencies
        
    Returns:
        SVG content with placeholders replaced
    """
    # Standardize data if needed
    standardized = standardize_data(data)
    
    # Get date
    date_str = standardized.get("date") or datetime.now().strftime("%Y-%m-%d")
    full_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    
    # Get currency rates
    currencies = standardized.get("currencies", {})
    usd_rate = currencies.get("USD", {}).get("rate") if currencies.get("USD") else None
    eur_rate = currencies.get("EUR", {}).get("rate") if currencies.get("EUR") else None
    jpy_rate = currencies.get("JPY", {}).get("rate") if currencies.get("JPY") else None
    cny_rate = currencies.get("CNY", {}).get("rate") if currencies.get("CNY") else None
    sgd_rate = currencies.get("SGD", {}).get("rate") if currencies.get("SGD") else None
    
    # Create replacement dictionary (prioritize double curly brackets)
    # Note: Template uses {{USD_RATE}} (no S), but we support both formats for compatibility
    replacements = {
        "{{FULL_DATE}}": full_date,
        "{{USD_RATE}}": format_rate(usd_rate),  # Template format (no S)
        "{{EUR_RATE}}": format_rate(eur_rate),  # Template format (no S)
        "{{JPY_RATE}}": format_rate(jpy_rate),  # Template format (no S)
        "{{CNY_RATE}}": format_rate(cny_rate),  # Template format (no S)
        "{{SGD_RATE}}": format_rate(sgd_rate),  # Template format (no S)
        "{{USD_RATES}}": format_rate(usd_rate),  # Alternative format (with S)
        "{{EUR_RATES}}": format_rate(eur_rate),  # Alternative format (with S)
        "{{JPY_RATES}}": format_rate(jpy_rate),  # Alternative format (with S)
        "{{CNY_RATES}}": format_rate(cny_rate),  # Alternative format (with S)
        "{{SGD_RATES}}": format_rate(sgd_rate),  # Alternative format (with S)
        "{FULL_DATE}": full_date,
        "{USD_RATE}": format_rate(usd_rate),
        "{EUR_RATE}": format_rate(eur_rate),
        "{JPY_RATE}": format_rate(jpy_rate),
        "{CNY_RATE}": format_rate(cny_rate),
        "{SGD_RATE}": format_rate(sgd_rate),
        "{USD_RATES}": format_rate(usd_rate),
        "{EUR_RATES}": format_rate(eur_rate),
        "{JPY_RATES}": format_rate(jpy_rate),
        "{CNY_RATES}": format_rate(cny_rate),
        "{SGD_RATES}": format_rate(sgd_rate),
        "{FULL_DATE}}": full_date,
        "{USD_RATE}}": format_rate(usd_rate),
        "{EUR_RATE}}": format_rate(eur_rate),
        "{JPY_RATE}}": format_rate(jpy_rate),
        "{CNY_RATE}}": format_rate(cny_rate),
        "{SGD_RATE}}": format_rate(sgd_rate),
        "{USD_RATES}}": format_rate(usd_rate),
        "{EUR_RATES}}": format_rate(eur_rate),
        "{JPY_RATES}}": format_rate(jpy_rate),
        "{CNY_RATES}}": format_rate(cny_rate),
        "{SGD_RATES}}": format_rate(sgd_rate),
    }
    
    result = svg_content
    
    # Find all text elements that might contain placeholders
    # Pattern matches <text>...</text> including nested tspan elements
    # Using non-greedy matching to handle multiple text elements correctly
    text_element_pattern = r'(<text[^>]*>)(.*?)(</text>)'
    
    def replace_in_text_element(match):
        """Replace placeholders within a text element."""
        opening_tag = match.group(1)
        content = match.group(2)
        closing_tag = match.group(3)
        
        # Extract full text content (handling tspan elements)
        # This reconstructs text that was split across <tspan> elements
        full_text = extract_text_from_element(content)
        
        # Check if this text element contains any placeholder
        has_placeholder = any(ph in full_text for ph in replacements.keys())
        
        if has_placeholder:
            # Replace placeholders in the extracted text
            new_text = full_text
            for placeholder, value in replacements.items():
                new_text = new_text.replace(placeholder, str(value))
            
            # Rebuild the text element with the new text
            # Use simple text content (no tspan) to avoid rendering issues
            # This ensures the text renders as a single continuous string
            return f"{opening_tag}{new_text}{closing_tag}"
        else:
            # No placeholder, return original
            return match.group(0)
    
    # Replace placeholders in text elements
    # Use DOTALL flag to handle multiline text elements
    result = re.sub(text_element_pattern, replace_in_text_element, result, flags=re.DOTALL)
    
    # Also do simple string replacement for any remaining placeholders
    # (e.g., in attributes, comments, etc.)
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    
    # Ensure Montserrat font is preserved (replace any accidental Helvetica)
    result = result.replace("font-family:'Helvetica'", "font-family:'Montserrat'")
    result = result.replace('font-family:"Helvetica"', 'font-family:"Montserrat"')
    
    return result


def generate_forex_svg(template_path, output_dir="data/forex_data", standardized_data=None):
    """
    Generate SVG file from template with daily forex data.
    
    Args:
        template_path: Path to the SVG template file
        output_dir: Directory to save the generated SVG
        standardized_data: Optional pre-standardized data dictionary. If None, fetches fresh data.
        
    Returns:
        Path to the generated SVG file
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
    svg_content = replace_svg_placeholders(template_content, standardized_data)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename with date
    date_str = standardized_data.get("date") or datetime.now().strftime("%Y-%m-%d")
    output_filename = f"forex_{date_str}.svg"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save generated SVG
    print(f"Saving to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"✓ SVG generated successfully: {output_path}")
    return output_path


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate SVG from template with daily forex data"
    )
    parser.add_argument(
        "template",
        nargs="?",
        help="Path to SVG template file (default: templates/forex_template.svg)"
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
        # Try common locations
        possible_paths = [
            "templates/forex_template.svg",
            "templates/Carouselle Cover-1.svg",
            "forex_template.svg",
            "template.svg"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            print("Error: No template file specified and no default template found.")
            print("Please provide the template path as an argument or place it at:")
            print("  - templates/forex_template.svg")
            print("  - forex_template.svg")
            print("  - template.svg")
            sys.exit(1)
    
    try:
        generate_forex_svg(template_path, args.output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


