"""
Commodity Collector Module

This module handles fetching mineral commodity prices from Metals.Dev API.
Tracks: Gold, Silver, Copper, Aluminium, Nickel in AUD.
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config
try:
    from config import settings
except ImportError:
    try:
        import config.settings as settings
    except ImportError:
        print("Warning: Could not import settings. Make sure config/settings.py exists.")
        settings = None


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


def fetch_metals_dev_data() -> Optional[Dict[str, Any]]:
    """
    Fetch all commodity prices from Metals.Dev API in a single request.
    Requests prices directly in AUD to avoid currency conversion.
    
    Returns:
        API response dictionary, or None if failed
    """
    api_key = None
    if settings and hasattr(settings, 'METALS_DEV_API_KEY'):
        api_key = settings.METALS_DEV_API_KEY
    
    if not api_key or api_key == "your_metals_dev_api_key_here":
        print("Error: METALS_DEV_API_KEY not configured in config/settings.py")
        print("Please add your API key from https://metals.dev/dashboard")
        return None
    
    # Use query parameters for API key and request prices in AUD
    url = f"https://api.metals.dev/v1/latest?api_key={api_key}&currency=AUD"
    
    try:
        print("Fetching commodity prices from Metals.Dev API (in AUD)...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success":
            print(f"Error: API returned status: {data.get('status')}")
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Metals.Dev API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return None


def extract_commodity_prices(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract commodity prices from Metals.Dev API response.
    
    Since we request prices in AUD, prices are already in AUD (no conversion needed).
    Maps API symbols to our internal commodity names:
    - gold -> GOLD
    - silver -> SILVER
    - copper -> COPPER
    - aluminum -> ALUMINIUM
    - nickel -> NICKEL
    
    Args:
        api_data: Response from Metals.Dev API (prices in AUD)
        
    Returns:
        Dictionary with commodity prices in our standard format
    """
    metals = api_data.get("metals", {})
    
    # Get USD/AUD rate for price_usd calculation (optional, for reference)
    aud_per_usd = get_usd_aud_rate()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().isoformat()
    
    # Map Metals.Dev symbols (all lowercase) to our commodity names
    commodity_mapping = {
        "GOLD": "gold",
        "SILVER": "silver",
        "COPPER": "copper",
        "ALUMINIUM": "aluminum",  # API uses "aluminum" (US spelling)
        "NICKEL": "nickel"
    }
    
    commodities_data = {}
    
    for commodity_name, api_symbol in commodity_mapping.items():
        # Prices are already in AUD when currency=AUD is specified
        price_aud = metals.get(api_symbol)
        
        if price_aud is None:
            print(f"Warning: Could not find price for {commodity_name} (symbol: {api_symbol}) in API response")
            commodities_data[commodity_name] = {
                "price_aud": None,
                "price_usd": None,
                "unit": "oz" if commodity_name in ["GOLD", "SILVER"] else "mt",
                "currency": "AUD",
                "date": date_str,
                "error": f"Price not found in API response"
            }
            continue
        
        # Calculate USD price for reference (optional)
        price_usd = price_aud / aud_per_usd if aud_per_usd else None
        
        # Determine unit
        # Metals.Dev returns Gold/Silver in Troy Ounces, Base Metals in Tonnes
        unit = "oz" if commodity_name in ["GOLD", "SILVER"] else "mt"
        
        print(f"  ✓ {commodity_name}: ${price_aud:,.2f} AUD ({unit})")
        
        commodities_data[commodity_name] = {
            "price_usd": price_usd,
            "price_aud": price_aud,
            "unit": unit,
            "currency": "AUD",
            "date": date_str,
            "source": "Metals.Dev"
        }
    
    return {
        "timestamp": timestamp_str,
        "commodities": commodities_data
    }


def fetch_commodity_prices() -> Dict[str, Any]:
    """
    Fetch mineral commodity prices in AUD from Metals.Dev API.
    Tracks: Gold, Silver, Copper, Aluminium, Nickel.
    
    Returns:
        Dictionary with commodity prices and metadata
    """
    api_data = fetch_metals_dev_data()
    
    if not api_data:
        # Return empty structure on failure
        date_str = datetime.now().strftime("%Y-%m-%d")
        return {
            "timestamp": datetime.now().isoformat(),
            "commodities": {
                "GOLD": {"price_aud": None, "price_usd": None, "unit": "oz", "currency": "AUD", "date": date_str, "error": "API request failed"},
                "SILVER": {"price_aud": None, "price_usd": None, "unit": "oz", "currency": "AUD", "date": date_str, "error": "API request failed"},
                "COPPER": {"price_aud": None, "price_usd": None, "unit": "mt", "currency": "AUD", "date": date_str, "error": "API request failed"},
                "ALUMINIUM": {"price_aud": None, "price_usd": None, "unit": "mt", "currency": "AUD", "date": date_str, "error": "API request failed"},
                "NICKEL": {"price_aud": None, "price_usd": None, "unit": "mt", "currency": "AUD", "date": date_str, "error": "API request failed"}
            }
        }
    
    return extract_commodity_prices(api_data)


def fetch_metals_dev_timeseries(start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """
    Fetch commodity prices from Metals.Dev API timeseries endpoint for a date range.
    This is more efficient than making multiple API calls for different dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        API response dictionary with rates for each date, or None if failed
    """
    api_key = None
    if settings and hasattr(settings, 'METALS_DEV_API_KEY'):
        api_key = settings.METALS_DEV_API_KEY
    
    if not api_key or api_key == "your_metals_dev_api_key_here":
        print("Error: METALS_DEV_API_KEY not configured in config/settings.py")
        print("Please add your API key from https://metals.dev/dashboard")
        return None
    
    # Use timeseries endpoint for date range
    url = f"https://api.metals.dev/v1/timeseries?api_key={api_key}&start_date={start_date}&end_date={end_date}&currency=AUD"
    
    try:
        print(f"Fetching commodity prices from Metals.Dev API timeseries (in AUD)...")
        print(f"  Date range: {start_date} to {end_date}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success":
            error_msg = data.get("error_message", "Unknown error")
            print(f"Error: API returned status: {data.get('status')}")
            print(f"Error message: {error_msg}")
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Metals.Dev API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return None


def extract_timeseries_commodity_prices(api_data: Dict[str, Any], date_str: str) -> Dict[str, Any]:
    """
    Extract commodity prices for a specific date from Metals.Dev timeseries API response.
    
    The timeseries API returns prices in USD (even when AUD is requested), so we need to:
    1. Extract prices from the "metals" object
    2. Convert USD prices to AUD using the exchange rate from the response
    
    Args:
        api_data: Response from Metals.Dev timeseries API
        date_str: Date in YYYY-MM-DD format to extract prices for
    
    Returns:
        Dictionary with commodity prices in our standard format for the specified date
    """
    rates = api_data.get("rates", {})
    date_prices = rates.get(date_str)
    
    if not date_prices:
        # Return empty structure if date not found
        return {
            "timestamp": datetime.now().isoformat(),
            "commodities": {
                "GOLD": {"price_aud": None, "price_usd": None, "unit": "oz", "currency": "AUD", "date": date_str, "error": f"Date {date_str} not found in API response"},
                "SILVER": {"price_aud": None, "price_usd": None, "unit": "oz", "currency": "AUD", "date": date_str, "error": f"Date {date_str} not found in API response"},
                "COPPER": {"price_aud": None, "price_usd": None, "unit": "mt", "currency": "AUD", "date": date_str, "error": f"Date {date_str} not found in API response"},
                "ALUMINIUM": {"price_aud": None, "price_usd": None, "unit": "mt", "currency": "AUD", "date": date_str, "error": f"Date {date_str} not found in API response"},
                "NICKEL": {"price_aud": None, "price_usd": None, "unit": "mt", "currency": "AUD", "date": date_str, "error": f"Date {date_str} not found in API response"}
            }
        }
    
    # Extract metals prices (in USD) and currency exchange rates
    metals = date_prices.get("metals", {})
    currencies = date_prices.get("currencies", {})
    
    # Get USD/AUD exchange rate from the response
    # The currencies object has AUD as a key with value like 0.6666 (meaning 1 USD = 0.6666 AUD)
    # So 1 AUD = 1 / 0.6666 USD = 1.5 USD (approximately)
    usd_per_aud = currencies.get("AUD")
    if usd_per_aud and usd_per_aud > 0:
        aud_per_usd = 1.0 / usd_per_aud
    else:
        # Fallback to external API if not in response
        aud_per_usd = get_usd_aud_rate()
    
    timestamp_str = datetime.now().isoformat()
    
    # Map Metals.Dev symbols (all lowercase) to our commodity names
    # Note: Timeseries API may only return gold and silver in the metals object
    commodity_mapping = {
        "GOLD": "gold",
        "SILVER": "silver",
        "COPPER": "copper",
        "ALUMINIUM": "aluminum",  # API uses "aluminum" (US spelling)
        "NICKEL": "nickel"
    }
    
    commodities_data = {}
    
    for commodity_name, api_symbol in commodity_mapping.items():
        # Prices are in USD from the timeseries API (even when AUD is requested)
        price_usd = metals.get(api_symbol)
        
        if price_usd is None:
            # Base metals (copper, aluminum, nickel) may not be available in timeseries endpoint
            if commodity_name in ["COPPER", "ALUMINIUM", "NICKEL"]:
                print(f"  Note: {commodity_name} not available in timeseries API for {date_str}")
            else:
                print(f"  Warning: Could not find price for {commodity_name} (symbol: {api_symbol}) for date {date_str}")
            
            commodities_data[commodity_name] = {
                "price_aud": None,
                "price_usd": None,
                "unit": "oz" if commodity_name in ["GOLD", "SILVER"] else "mt",
                "currency": "AUD",
                "date": date_str,
                "error": f"Price not found in API response"
            }
            continue
        
        # Convert USD price to AUD
        price_aud = price_usd * aud_per_usd if aud_per_usd else None
        
        # Determine unit
        # Metals.Dev returns Gold/Silver in Troy Ounces, Base Metals in Tonnes
        unit = "oz" if commodity_name in ["GOLD", "SILVER"] else "mt"
        
        commodities_data[commodity_name] = {
            "price_usd": price_usd,
            "price_aud": price_aud,
            "unit": unit,
            "currency": "AUD",
            "date": date_str,
            "source": "Metals.Dev"
        }
    
    return {
        "timestamp": timestamp_str,
        "commodities": commodities_data
    }


def fetch_base_metals_yfinance(date_str: str) -> Dict[str, Any]:
    """
    Fetch base metals prices (Copper, Aluminium, Nickel) from yfinance for a specific date.
    Prices are fetched in USD and converted to AUD.
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        Dictionary with base metals prices in AUD
    """
    try:
        import yfinance as yf
    except ImportError:
        print("Warning: yfinance not installed. Install with: pip install yfinance")
        return {}
    
    # Get USD/AUD exchange rate for conversion
    aud_per_usd = get_usd_aud_rate()
    
    base_metals = {}
    
    # Yahoo Finance tickers for base metals futures
    # Note: Some metals may not have direct futures, we'll try common ones
    tickers = {
        "COPPER": "HG=F",  # Copper Futures
        # Aluminium and Nickel may not have direct futures on Yahoo Finance
        # We'll try alternative tickers or leave as None
    }
    
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # yfinance needs a date range, so get a few days around the target date
        start_date = (date_obj - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Fetch copper price
        if "COPPER" in tickers:
            try:
                ticker = yf.Ticker(tickers["COPPER"])
                # Get historical data for the date range
                hist = ticker.history(start=start_date, end=end_date, interval="1d")
                
                if not hist.empty:
                    # Find the closest date to our target date
                    hist.index = hist.index.tz_localize(None)  # Remove timezone
                    target_date = date_obj.date()
                    
                    # Find the row closest to our target date
                    closest_idx = None
                    min_diff = None
                    for idx in hist.index:
                        diff = abs((idx.date() - target_date).days)
                        if min_diff is None or diff < min_diff:
                            min_diff = diff
                            closest_idx = idx
                    
                    if closest_idx is not None and min_diff <= 5:  # Within 5 days
                        # Get closing price (in USD per pound typically)
                        price_usd_per_lb = hist.loc[closest_idx, 'Close']
                        # Convert to USD per metric tonne (1 metric tonne = 2204.62 pounds)
                        price_usd_per_mt = price_usd_per_lb * 2204.62
                        # Convert to AUD
                        price_aud_per_mt = price_usd_per_mt * aud_per_usd
                        
                        base_metals["COPPER"] = {
                            "price_usd": price_usd_per_mt,
                            "price_aud": price_aud_per_mt,
                            "unit": "mt",
                            "currency": "AUD",
                            "date": date_str,
                            "source": "yfinance"
                        }
                        print(f"  ✓ COPPER: ${price_aud_per_mt:,.2f} AUD/mt (from yfinance, date: {closest_idx.date()})")
                    else:
                        print(f"  Warning: No COPPER data found near {date_str}")
            except Exception as e:
                print(f"  Warning: Could not fetch COPPER from yfinance: {e}")
        
        # For Aluminium, try LME aluminium price (may need different approach)
        # Yahoo Finance doesn't have direct aluminium futures, but we can try alternative sources
        # For now, we'll note it's not available via yfinance
        
        # For Nickel, try LME nickel if available
        # Yahoo Finance doesn't have direct nickel futures either
        # These would typically require LME (London Metal Exchange) data or other sources
            
    except Exception as e:
        print(f"Warning: Error fetching base metals from yfinance: {e}")
    
    return base_metals


def collect_all_commodity_data() -> Dict[str, Any]:
    """
    Collect all commodity data (Gold, Silver, Copper, Aluminium, Nickel).
    
    Returns:
        Dataset with commodity prices
    """
    print("Collecting commodity prices from Metals.Dev API...")
    data = fetch_commodity_prices()
    
    return {
        "collection_date": datetime.now().isoformat(),
        "commodities": data
    }


if __name__ == "__main__":
    # Test the data collection
    print("Testing commodity data collection...")
    data = collect_all_commodity_data()
    print("\nCollected Data:")
    print(json.dumps(data, indent=2))
