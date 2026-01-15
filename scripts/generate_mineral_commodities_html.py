#!/usr/bin/env python3
"""
Generate Mineral Commodities HTML from Template

This script reads an HTML template with placeholders and replaces them with
daily mineral commodity data, then saves the result to data/commodities_data/HTML/ and also
converts it to JPEG format saved to data/commodities_data/JPEG/.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.commodity_collector import collect_all_commodity_data
from src.commodity_formatter import standardize_commodity_data
from src.commodity_history import load_commodity_history_csv
import pandas as pd

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def format_price(price, decimals=2):
    """
    Format commodity price with specified decimal places.
    
    Args:
        price: The price value
        decimals: Number of decimal places (default: 2)
        
    Returns:
        Formatted price string
    """
    if price is None:
        return "N/A"
    return f"{price:,.{decimals}f}"


def get_previous_day_prices(current_date_str, csv_path="data/commodities_data/processed/commodity_daily.csv"):
    """
    Get commodity prices for the previous day (n-1).
    
    Args:
        current_date_str: Current date in YYYY-MM-DD format
        csv_path: Path to the commodity history CSV file
        
    Returns:
        Dictionary with commodity codes as keys and prices as values, or None if not found
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
        
        df = load_commodity_history_csv(csv_path)
        
        if df is None or df.empty:
            return None
        
        # Parse current date
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        
        # Find previous day (go back up to 7 days to find the most recent data)
        previous_prices = None
        for days_back in range(1, 8):
            check_date = current_date - timedelta(days=days_back)
            previous_row = df[df['date'] == check_date]
            
            if not previous_row.empty:
                row = previous_row.iloc[0]
                previous_prices = {
                    "GOLD": row.get('gold_price') if pd.notna(row.get('gold_price')) else None,
                    "SILVER": row.get('silver_price') if pd.notna(row.get('silver_price')) else None,
                    "COPPER": row.get('copper_price') if pd.notna(row.get('copper_price')) else None,
                    "ALUMINIUM": row.get('aluminium_price') if pd.notna(row.get('aluminium_price')) else None,
                    "ZINC": row.get('zinc_price') if pd.notna(row.get('zinc_price')) else None,
                    "NICKEL": row.get('nickel_price') if pd.notna(row.get('nickel_price')) else None,
                }
                # Verify we got at least one valid price
                if any(v is not None for v in previous_prices.values()):
                    return previous_prices
        
        return None
    except Exception as e:
        print(f"Warning: Could not load previous day's prices: {e}")
        return None


def generate_arrow_html(current_price, previous_price):
    """
    Generate arrow HTML based on price comparison.
    
    Args:
        current_price: Current day's price
        previous_price: Previous day's price
        
    Returns:
        HTML string for the arrow icon, or empty string if no comparison possible
    """
    if current_price is None or previous_price is None:
        return ""
    
    try:
        current = float(current_price)
        previous = float(previous_price)
        
        if current > previous:
            # Price is up - green up arrow
            return '<div class="commodity-arrow arrow-up"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7 14L12 9L17 14H7Z" fill="currentColor"/></svg></div>'
        elif current < previous:
            # Price is down - red down arrow
            return '<div class="commodity-arrow arrow-down"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7 10L12 15L17 10H7Z" fill="currentColor"/></svg></div>'
        else:
            # No change - white dash
            return '<div class="commodity-arrow arrow-neutral"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><line x1="7" y1="12" x2="17" y2="12" stroke="currentColor" stroke-width="3"/></svg></div>'
    except (ValueError, TypeError):
        return ""


def replace_html_placeholders(html_content, data, include_arrows=False):
    """
    Replace placeholders in HTML content with actual commodity data.
    
    Args:
        html_content: The HTML template content as string
        data: Standardized data dictionary with commodities
        include_arrows: Whether to include arrow placeholders (for arrow template)
        
    Returns:
        HTML content with placeholders replaced
    """
    # Preserve the date from input data if it exists (for historical dates)
    preserved_date = data.get("date") if isinstance(data, dict) else None
    
    # Standardize data if needed
    standardized = standardize_commodity_data(data)
    
    # Use preserved date if available, otherwise use standardized date, otherwise today
    date_str = preserved_date or standardized.get("date") or datetime.now().strftime("%Y-%m-%d")
    # Ensure standardized data uses the correct date
    standardized["date"] = date_str
    
    full_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    
    # Get commodity prices
    commodities = standardized.get("commodities", {})
    prices = {
        "GOLD": commodities.get("GOLD", {}).get("price_aud") if commodities.get("GOLD") else None,
        "SILVER": commodities.get("SILVER", {}).get("price_aud") if commodities.get("SILVER") else None,
        "COPPER": commodities.get("COPPER", {}).get("price_aud") if commodities.get("COPPER") else None,
        "ALUMINIUM": commodities.get("ALUMINIUM", {}).get("price_aud") if commodities.get("ALUMINIUM") else None,
        "ZINC": commodities.get("ZINC", {}).get("price_aud") if commodities.get("ZINC") else None,
        "NICKEL": commodities.get("NICKEL", {}).get("price_aud") if commodities.get("NICKEL") else None,
    }
    
    # Get previous day's prices if arrows are needed
    previous_prices = None
    if include_arrows:
        previous_prices = get_previous_day_prices(date_str)
        if previous_prices:
            print(f"  Found previous day's prices for comparison")
        else:
            print(f"  Warning: No previous day's prices found - arrows will not be displayed")
    
    # Build replacement dictionary
    replacements = {
        "{{FULL_DATE}}": full_date,
        "{FULL_DATE}": full_date,
    }
    
    for commodity in ["GOLD", "SILVER", "COPPER", "ALUMINIUM", "ZINC", "NICKEL"]:
        price_value = format_price(prices[commodity], decimals=2)
        replacements["{{" + commodity + "_RATE}}"] = price_value
        replacements["{" + commodity + "_RATE}"] = price_value
        
        # Add arrow if needed
        if include_arrows:
            arrow_html = ""
            if previous_prices and previous_prices.get(commodity) is not None:
                arrow_html = generate_arrow_html(prices[commodity], previous_prices.get(commodity))
                if arrow_html:
                    direction = "up" if prices[commodity] and previous_prices.get(commodity) and float(prices[commodity]) > float(previous_prices.get(commodity)) else "down"
                    print(f"  {commodity}: {price_value} ({direction} from previous day)")
            else:
                print(f"  {commodity}: {price_value} (no previous data for comparison)")
            replacements["{{" + commodity + "_ARROW}}"] = arrow_html
            replacements["{" + commodity + "_ARROW}"] = arrow_html
    
    # Replace all placeholders
    result = html_content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    
    return result


def html_to_jpeg(html_path, jpeg_path, width=1080, height=1350):
    """
    Convert HTML file to JPEG image.
    
    Args:
        html_path: Path to the HTML file
        jpeg_path: Path where the JPEG should be saved
        width: Width of the output image in pixels (default: 1080)
        height: Height of the output image in pixels (default: 1350)
        
    Returns:
        Path to the generated JPEG file, or None if conversion failed
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("Warning: playwright not available. Install with: pip install playwright && playwright install chromium")
        return None
    
    try:
        with sync_playwright() as p:
            # Launch browser (try chromium, firefox, then webkit)
            browser = None
            for browser_type in [p.chromium, p.firefox, p.webkit]:
                try:
                    browser = browser_type.launch()
                    break
                except Exception:
                    continue
            
            if browser is None:
                raise Exception("Could not launch any browser (chromium, firefox, or webkit)")
            
            page = browser.new_page()
            
            # Set viewport size to match HTML dimensions
            page.set_viewport_size({"width": width, "height": height})
            
            # Load HTML file (use file:// URL format)
            html_abs_path = os.path.abspath(html_path)
            # Convert Windows path separators to forward slashes for file:// URL
            html_file_url = f"file://{html_abs_path.replace(os.sep, '/')}"
            page.goto(html_file_url)
            
            # Wait for page to load (including fonts and images)
            page.wait_for_load_state("networkidle")
            
            # Take full page screenshot as JPEG (captures entire content, not just viewport)
            page.screenshot(path=jpeg_path, type="jpeg", quality=95, full_page=True)
            
            browser.close()
        
        print(f"✓ JPEG generated successfully: {jpeg_path}")
        return jpeg_path
    except Exception as e:
        print(f"Warning: Error converting HTML to JPEG: {e}")
        return None


def generate_mineral_commodities_html(template_path, output_dir="data/commodities_data", standardized_data=None):
    """
    Generate HTML file from template with daily mineral commodity data.
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
    if standardized_data is None:
        print("Fetching daily commodity prices...")
        data = collect_all_commodity_data()
        
        # Standardize data
        standardized_data = standardize_commodity_data({
            "collection_date": datetime.now().isoformat(),
            "commodities": data.get("commodities", {})
        })
    else:
        print("Using provided commodity data...")
    
    # Check if template has arrow placeholders by looking for ARROW placeholders in the content
    is_arrow_template = any(f"{{{{{commodity}_ARROW}}}}" in template_content or 
                            f"{{{commodity}_ARROW}}" in template_content
                            for commodity in ["GOLD", "SILVER", "COPPER", "ALUMINIUM", "ZINC", "NICKEL"])
    
    if is_arrow_template:
        print("Arrow placeholders detected in template - will include arrows based on previous day's prices")
    
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
    output_filename = f"commodity_{date_str}.html"
    html_path = os.path.join(html_dir, output_filename)
    jpeg_filename = f"commodity_{date_str}.jpg"
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


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate HTML from template with daily mineral commodity data"
    )
    parser.add_argument(
        "template",
        nargs="?",
        help="Path to HTML template file (default: templates/mineral_commodities_template.html)"
    )
    parser.add_argument(
        "-o", "--output",
        default="data/mineral_commodities",
        help="Output directory (default: data/mineral_commodities)"
    )
    
    args = parser.parse_args()
    
    # Default template path if not provided
    template_path = args.template
    if not template_path:
        possible_paths = [
            "templates/mineral_commodities_template.html",
            "mineral_commodities_template.html",
            "template.html"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            print("Error: No template file specified and no default template found.")
            print("Please provide the template path as an argument or place it at:")
            print("  - templates/mineral_commodities_template.html")
            print("  - mineral_commodities_template.html")
            sys.exit(1)
    
    try:
        generate_mineral_commodities_html(template_path, args.output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
