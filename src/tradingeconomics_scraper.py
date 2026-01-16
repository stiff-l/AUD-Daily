"""
TradingEconomics Scraper Module

This module handles scraping commodity prices from TradingEconomics.com
using CloudScraper (with Selenium fallback) to bypass anti-bot protection.
Tracks: Gold, Silver, Copper, Aluminium, Nickel
"""

import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import cloudscraper first (preferred)
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("Warning: cloudscraper not available. Install with: pip install cloudscraper")

# Try to import selenium as fallback
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: selenium not available. Install with: pip install selenium")

# Fallback to requests if neither is available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Error: requests not available. Install with: pip install requests")

# Try to import BeautifulSoup for better HTML parsing
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("Note: BeautifulSoup not available. Install with: pip install beautifulsoup4 for better parsing")


def get_usd_aud_rate() -> float:
    """
    Get current USD/AUD exchange rate for price conversion.
    
    Returns:
        USD/AUD rate (e.g., 0.68 means 1 USD = 0.68 AUD, so 1 AUD = 1.47 USD)
    """
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/AUD", timeout=10)
        response.raise_for_status()
        rates = response.json()
        usd_rate = rates.get("rates", {}).get("USD", None)
        
        if usd_rate:
            # Convert: 1 USD = 1/usd_rate AUD, so aud_per_usd = 1/usd_rate
            return 1.0 / usd_rate
    except Exception as e:
        print(f"Warning: Could not fetch USD/AUD rate: {e}")
    
    # Fallback rate
    return 1.47


def scrape_with_cloudscraper(url: str, timeout: int = 30) -> Optional[str]:
    """
    Scrape a URL using CloudScraper.
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string, or None if failed
    """
    if not CLOUDSCRAPER_AVAILABLE:
        return None
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        response = scraper.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"CloudScraper error for {url}: {e}")
        return None


def scrape_with_selenium(url: str, timeout: int = 30) -> Optional[str]:
    """
    Scrape a URL using Selenium (fallback method).
    
    Args:
        url: URL to scrape
        timeout: Page load timeout in seconds
        
    Returns:
        HTML content as string, or None if failed
    """
    if not SELENIUM_AVAILABLE:
        return None
    
    driver = None
    try:
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        driver.get(url)
        
        # Wait for page to load (look for price elements)
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Additional wait for dynamic content
            time.sleep(2)
        except:
            pass
        
        html_content = driver.page_source
        return html_content
    except Exception as e:
        print(f"Selenium error for {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def scrape_with_requests(url: str, timeout: int = 30) -> Optional[str]:
    """
    Scrape a URL using requests (basic fallback).
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string, or None if failed
    """
    if not REQUESTS_AVAILABLE:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Requests error for {url}: {e}")
        return None


def extract_price_from_html(html: str, commodity_name: str) -> Optional[float]:
    """
    Extract commodity price from TradingEconomics HTML.
    
    TradingEconomics typically displays prices in various formats.
    We'll look for common patterns like:
    - Price in USD (e.g., "2,345.67" or "2345.67")
    - Price elements with specific classes/IDs
    - JSON data embedded in the page
    
    Args:
        html: HTML content from the page
        commodity_name: Name of the commodity (for debugging)
        
    Returns:
        Price as float in USD, or None if not found
    """
    if not html:
        return None
    
    # Define commodity-specific price ranges (in USD)
    commodity_ranges = {
        'gold': (1000, 5000),      # Gold typically $1000-$5000/oz
        'silver': (10, 100),       # Silver typically $10-$100/oz
        'copper': (3, 15000),      # Copper: $3-$5/lb (displayed) or $5000-$15000/mt - accept wider range
        'aluminum': (1000, 5000),  # Aluminum typically $1000-$5000/mt
        'aluminium': (1000, 5000), # Aluminium (UK spelling)
        'nickel': (10000, 30000),  # Nickel typically $10000-$30000/mt
    }
    
    name_lower = commodity_name.lower()
    min_price, max_price = commodity_ranges.get(name_lower, (0.01, 1000000))
    
    # Filter out common non-price values (like exchange rates, percentages, etc.)
    excluded_ranges = [
        (50, 80),      # Common exchange rate range (e.g., USD/AUD around 0.65-0.75)
        (0, 1),        # Percentages and small decimals
        (100, 200),    # Common page element IDs
    ]
    
    def is_valid_price(price: float) -> bool:
        """Check if price is within valid range and not excluded"""
        if not (min_price <= price <= max_price):
            return False
        # Exclude common non-price values
        for excl_min, excl_max in excluded_ranges:
            if excl_min <= price <= excl_max:
                return False
        return True
    
    # Strategy 1: Look for JSON data embedded in script tags (most reliable)
    if BEAUTIFULSOUP_AVAILABLE:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Look for JSON objects with price data
                json_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                    r'window\.__DATA__\s*=\s*({.+?});',
                    r'var\s+data\s*=\s*({.+?});',
                    r'const\s+data\s*=\s*({.+?});',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, script_text, re.DOTALL)
                    for match in matches:
                        try:
                            import json
                            data = json.loads(match)
                            # Try various paths in the JSON
                            paths = [
                                ['market', 'price'],
                                ['commodity', 'price'],
                                ['data', 'price'],
                                ['quote', 'price'],
                                ['lastPrice'],
                                ['last'],
                                ['value'],
                                ['price'],
                            ]
                            for path in paths:
                                value = data
                                for key in path:
                                    if isinstance(value, dict) and key in value:
                                        value = value[key]
                                    else:
                                        value = None
                                        break
                                if value and isinstance(value, (int, float)):
                                    price = float(value)
                                    if is_valid_price(price):
                                        return price
                        except:
                            continue
                
                # Look for direct price patterns in script
                price_patterns = [
                    r'"price"\s*:\s*([0-9,]+\.?[0-9]*)',
                    r'"lastPrice"\s*:\s*([0-9,]+\.?[0-9]*)',
                    r'"last"\s*:\s*([0-9,]+\.?[0-9]*)',
                    r'"value"\s*:\s*([0-9,]+\.?[0-9]*)',
                ]
                for pattern in price_patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            price = float(match.replace(',', ''))
                            if is_valid_price(price):
                                return price
                        except:
                            continue
        except Exception as e:
            print(f"    BeautifulSoup JSON parsing error: {e}")
    
    # Strategy 2: Use BeautifulSoup to find price elements with specific TradingEconomics patterns
    if BEAUTIFULSOUP_AVAILABLE:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for TradingEconomics-specific class patterns
            te_selectors = [
                {'class': re.compile(r'market-price|quote-price|commodity-price', re.I)},
                {'class': re.compile(r'price-value|last-price', re.I)},
                {'class': re.compile(r'te-market-price', re.I)},
                {'id': re.compile(r'price|lastPrice|marketPrice', re.I)},
                {'data-price': True},
                {'data-value': True},
                {'data-last': True},
            ]
            
            for selector in te_selectors:
                elements = soup.find_all(attrs=selector)
                for elem in elements:
                    # Try data attributes first
                    for attr in ['data-price', 'data-value', 'data-last', 'data-lastprice']:
                        attr_value = elem.get(attr)
                        if attr_value:
                            try:
                                price = float(str(attr_value).replace(',', ''))
                                if is_valid_price(price):
                                    return price
                            except:
                                pass
                    
                    # Try text content
                    text = elem.get_text(strip=True)
                    # Look for price pattern in text
                    price_match = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)', text)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', ''))
                            if is_valid_price(price):
                                return price
                        except:
                            continue
        except Exception as e:
            print(f"    BeautifulSoup element parsing error: {e}")
    
    # Strategy 3: Regex patterns for price elements (with commodity-specific filtering)
    patterns = [
        # Look for price in various data attributes
        r'data-price=["\']([0-9,]+\.?[0-9]*)["\']',
        r'data-value=["\']([0-9,]+\.?[0-9]*)["\']',
        r'data-last=["\']([0-9,]+\.?[0-9]*)["\']',
        r'data-lastprice=["\']([0-9,]+\.?[0-9]*)["\']',
        # Look for price in span/div with price-related classes
        r'<span[^>]*class="[^"]*price[^"]*"[^>]*>([0-9,]+\.?[0-9]*)</span>',
        r'<div[^>]*class="[^"]*price[^"]*"[^>]*>([0-9,]+\.?[0-9]*)</div>',
        r'<span[^>]*class="[^"]*last[^"]*"[^>]*>([0-9,]+\.?[0-9]*)</span>',
        # Look for price near "Last" or "Price" text
        r'(?:Last|Price|Value)[\s:]*\$?\s*([0-9,]+\.?[0-9]*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            try:
                price_str = match.replace(',', '').strip()
                price = float(price_str)
                if is_valid_price(price):
                    return price
            except (ValueError, AttributeError):
                continue
    
    # Strategy 4: Last resort - look for reasonable prices in main content area
    # Try to find main content and extract prices from there
    if BEAUTIFULSOUP_AVAILABLE:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Look for main content areas
            main_content = soup.find('main') or soup.find('div', class_=re.compile(r'content|main|market', re.I))
            if main_content:
                text_content = main_content.get_text()
            else:
                text_content = soup.get_text()
        except:
            text_content = re.sub(r'<[^>]+>', ' ', html)
    else:
        text_content = re.sub(r'<[^>]+>', ' ', html)
    
    # Look for prices in text, prioritizing commodity-specific ranges
    price_pattern = r'\b([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)\b'
    matches = re.findall(price_pattern, text_content)
    
    # Collect all potential prices in valid range
    potential_prices = []
    for match in matches:
        try:
            price = float(match.replace(',', ''))
            if is_valid_price(price):
                potential_prices.append(price)
        except:
            continue
    
    # Return the first valid price found, or the one closest to expected range
    if potential_prices:
        # Prefer prices closer to the middle of the expected range
        expected_mid = (min_price + max_price) / 2
        potential_prices.sort(key=lambda p: abs(p - expected_mid))
        return potential_prices[0]
    
    print(f"Warning: Could not extract price for {commodity_name}")
    return None


def scrape_commodity_price(commodity_url: str, commodity_name: str) -> Optional[Dict[str, Any]]:
    """
    Scrape a single commodity price from TradingEconomics.
    
    Args:
        commodity_url: URL to the commodity page
        commodity_name: Name of the commodity
        
    Returns:
        Dictionary with price data, or None if failed
    """
    print(f"  Scraping {commodity_name} from {commodity_url}...")
    
    # Try CloudScraper first
    html = scrape_with_cloudscraper(commodity_url)
    
    # Fallback to Selenium if CloudScraper fails
    if not html:
        print(f"    CloudScraper failed, trying Selenium...")
        html = scrape_with_selenium(commodity_url)
    
    # Fallback to requests if both fail
    if not html:
        print(f"    Selenium failed, trying basic requests...")
        html = scrape_with_requests(commodity_url)
    
    if not html:
        print(f"    Error: Could not fetch HTML for {commodity_name}")
        return None
    
    # Extract price from HTML
    price_usd = extract_price_from_html(html, commodity_name)
    
    if price_usd is None:
        print(f"    Warning: Could not extract price for {commodity_name}")
        return None
    
    # Use current date and exchange rate
    date_str = datetime.now().strftime("%Y-%m-%d")
    aud_per_usd = get_usd_aud_rate()
    
    # Convert to AUD
    price_aud = price_usd * aud_per_usd
    
    print(f"    ✓ {commodity_name}: ${price_usd:.2f} USD = ${price_aud:.2f} AUD")
    
    return {
        "price_usd": price_usd,
        "price_aud": price_aud,
        "currency": "AUD",
        "date": date_str,
        "source": "TradingEconomics"
    }


def scrape_all_commodities() -> Dict[str, Any]:
    """
    Scrape all commodity prices from TradingEconomics.
    
    Returns:
        Dictionary with all commodity data
    """
    commodities = {
        "GOLD": "https://tradingeconomics.com/commodity/gold",
        "SILVER": "https://tradingeconomics.com/commodity/silver",
        "COPPER": "https://tradingeconomics.com/commodity/copper",
        "ALUMINIUM": "https://tradingeconomics.com/commodity/aluminum",
        "NICKEL": "https://tradingeconomics.com/commodity/nickel",
    }
    
    print("Scraping commodity prices from TradingEconomics...")
    print(f"Using method: {'CloudScraper' if CLOUDSCRAPER_AVAILABLE else 'Selenium' if SELENIUM_AVAILABLE else 'Requests'}")
    print()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().isoformat()
    
    data = {
        "timestamp": timestamp_str,
        "commodities": {}
    }
    
    for commodity_name, url in commodities.items():
        commodity_data = scrape_commodity_price(url, commodity_name)
        if commodity_data:
            # Determine unit based on commodity
            if commodity_name in ["GOLD", "SILVER"]:
                unit = "oz"
            else:
                unit = "mt"  # metric ton
            
            data["commodities"][commodity_name] = {
                **commodity_data,
                "unit": unit
            }
        else:
            data["commodities"][commodity_name] = {
                "price_aud": None,
                "price_usd": None,
                "unit": "oz" if commodity_name in ["GOLD", "SILVER"] else "mt",
                "currency": "AUD",
                "date": date_str,
                "error": "Failed to scrape price"
            }
        
        # Small delay between requests to be respectful
        time.sleep(1)
    
    return data


if __name__ == "__main__":
    # Test the scraper
    print("Testing TradingEconomics scraper...")
    data = scrape_all_commodities()
    print("\nScraped Data:")
    import json
    print(json.dumps(data, indent=2))
