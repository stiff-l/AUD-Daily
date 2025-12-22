"""
Data Collector Module

This module handles fetching data from various APIs for:
- Currency exchange rates (USD, EUR, CNY)
- Commodity prices (Gold, Silver, Copper)
- Cryptocurrency prices (BTC, ETH, SOL, ZCASH)
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import settings
except ImportError:
    print("Warning: config/settings.py not found. Using example settings.")
    from config import settings_example as settings


def fetch_currency_rates() -> Dict[str, Any]:
    """
    Fetch AUD exchange rates against major currencies.
    
    Returns:
        Dictionary with currency rates and metadata
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "currencies": {}
    }
    
    # Example: Using a free API (exchangerate-api.com)
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/AUD", timeout=10)
        response.raise_for_status()
        rates = response.json()
        
        # Extract the currencies we care about
        for currency in ["USD", "EUR", "CNY"]:
            if currency in rates.get("rates", {}):
                data["currencies"][currency] = {
                    "rate": rates["rates"][currency],
                    "base": "AUD",
                    "date": rates.get("date", datetime.now().strftime("%Y-%m-%d"))
                }
    except Exception as e:
        print(f"Error fetching currency rates: {e}")
        data["error"] = str(e)
    
    return data


def fetch_commodity_prices() -> Dict[str, Any]:
    """
    Fetch commodity prices (Gold, Silver, Copper).
    
    Uses free APIs with optional API key support for better data quality.
    
    Returns:
        Dictionary with commodity prices and metadata
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "commodities": {}
    }
    
    try:
        # Get AUD to USD rate for conversion
        aud_response = requests.get("https://api.exchangerate-api.com/v4/latest/AUD", timeout=10)
        aud_response.raise_for_status()
        aud_rates = aud_response.json()
        usd_rate = aud_rates.get("rates", {}).get("USD", 1)
        
        # Try metals-api.com if API key is configured
        metals_api_key = getattr(settings, 'METALS_API_KEY', None)
        
        if metals_api_key and metals_api_key != "your_metals_api_key_here":
            # Use metals-api.com with API key (better data quality)
            base_url = "https://api.metals.live/v1/spot"
            commodities_map = {
                "GOLD": "gold",
                "SILVER": "silver",
                "COPPER": "copper"
            }
            
            for symbol, metal_name in commodities_map.items():
                try:
                    response = requests.get(
                        f"{base_url}/{metal_name}",
                        headers={"x-api-key": metals_api_key},
                        timeout=10
                    )
                    if response.status_code == 200:
                        price_data = response.json()
                        # Handle different response formats
                        price = None
                        if isinstance(price_data, dict):
                            price = price_data.get("price") or price_data.get("spot") or price_data.get("value")
                        elif isinstance(price_data, (int, float)):
                            price = price_data
                        
                        if price:
                            price_usd = float(price)
                            data["commodities"][symbol] = {
                                "price": price_usd,
                                "price_aud": price_usd / usd_rate if usd_rate else None,
                                "currency": "USD",
                                "unit": "oz" if symbol in ["GOLD", "SILVER"] else "lb",
                                "source": "metals-api.com"
                            }
                except Exception as e:
                    print(f"Warning: Could not fetch {symbol} from metals-api.com: {e}")
        
        # Fallback: Use free alternative APIs
        # Try using exchangerate-api.com with commodity codes
        commodities_map = {
            "GOLD": {"symbol": "XAU"},
            "SILVER": {"symbol": "XAG"},
            "COPPER": {"symbol": "XCU"}
        }
        
        for symbol, metal_info in commodities_map.items():
            if symbol not in data["commodities"]:
                price_usd = None
                source = None
                
                # Try exchangerate-api.com for precious metals (free, no key required)
                # Note: exchangerate-api.com may not support commodities directly
                # So we'll try alternative free sources
                
                # Try alternative: exchangerate.host (free, no key) - has commodity support
                try:
                    if symbol in ["GOLD", "SILVER"]:
                        # exchangerate.host supports XAU and XAG
                        metal_code = metal_info["symbol"]
                        # Fetch latest rates with commodity codes
                        response = requests.get(
                            f"https://api.exchangerate.host/latest?base=USD&symbols={metal_code}",
                            timeout=10
                        )
                        if response.status_code == 200:
                            rates_data = response.json()
                            if rates_data.get("success") and metal_code in rates_data.get("rates", {}):
                                rate = rates_data["rates"][metal_code]
                                # XAU/XAG rates are typically quoted as USD per oz, so invert if needed
                                # If rate < 1, it's likely 1/X, otherwise it's the price
                                if rate > 0:
                                    if rate < 1:
                                        price_usd = 1.0 / float(rate)
                                    else:
                                        price_usd = float(rate)
                                    source = "exchangerate.host"
                except Exception as e:
                    pass
                
                # Try alternative: exchangerate.host convert endpoint
                if not price_usd and symbol in ["GOLD", "SILVER"]:
                    try:
                        metal_code = metal_info["symbol"]
                        response = requests.get(
                            f"https://api.exchangerate.host/convert?from={metal_code}&to=USD&amount=1",
                            timeout=10
                        )
                        if response.status_code == 200:
                            conv_data = response.json()
                            if conv_data.get("success") and conv_data.get("result"):
                                price_usd = float(conv_data["result"])
                                source = "exchangerate.host"
                    except Exception as e:
                        pass
                
                # Try alternative: metals-api.com free endpoint (without auth)
                if not price_usd:
                    try:
                        metal_name = symbol.lower()
                        response = requests.get(
                            f"https://api.metals.live/v1/spot/{metal_name}",
                            timeout=10
                        )
                        if response.status_code == 200:
                            price_data = response.json()
                            if isinstance(price_data, dict):
                                price_usd = price_data.get("price") or price_data.get("spot") or price_data.get("value")
                            elif isinstance(price_data, (int, float)):
                                price_usd = float(price_data)
                            if price_usd:
                                source = "metals-api.com (free)"
                    except Exception as e:
                        pass
                
                # Try alternative: Use a free API that provides commodity prices
                # exchangerate-api.com doesn't support commodities, so we'll use a placeholder
                # Users can configure METALS_API_KEY for better data
                
                # Set the commodity data
                if price_usd and price_usd > 0:
                    data["commodities"][symbol] = {
                        "price": price_usd,
                        "price_aud": price_usd / usd_rate if usd_rate and usd_rate > 0 else None,
                        "currency": "USD",
                        "unit": "oz" if symbol in ["GOLD", "SILVER"] else "lb",
                        "source": source or "unknown"
                    }
                else:
                    # If all methods fail, provide helpful message
                    data["commodities"][symbol] = {
                        "price": None,
                        "price_aud": None,
                        "currency": "USD",
                        "unit": "oz" if symbol in ["GOLD", "SILVER"] else "lb",
                        "note": f"Free API not available for {symbol}. For commodity prices, configure METALS_API_KEY in config/settings.py (free at https://metals-api.com)"
                    }
        
        # Print helpful message if no data retrieved
        if not any(c.get("price") for c in data["commodities"].values()):
            print("\n" + "="*60)
            print("INFO: Commodity prices not available.")
            print("="*60)
            print("To enable commodity prices:")
            print("1. Visit https://metals-api.com and sign up for a free API key")
            print("2. Add your API key to config/settings.py:")
            print("   METALS_API_KEY = 'your_api_key_here'")
            print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error fetching commodity prices: {e}")
        data["error"] = str(e)
        # Set default structure
        for commodity in ["GOLD", "SILVER", "COPPER"]:
            if commodity not in data["commodities"]:
                data["commodities"][commodity] = {
                    "price": None,
                    "currency": "USD",
                    "unit": "oz" if commodity in ["GOLD", "SILVER"] else "lb"
                }
    
    return data


def fetch_crypto_prices() -> Dict[str, Any]:
    """
    Fetch cryptocurrency prices (BTC, ETH, SOL, ZCASH).
    
    Returns:
        Dictionary with cryptocurrency prices and metadata
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "cryptocurrencies": {}
    }
    
    # Example: Using CoinGecko free API
    try:
        # Get prices for multiple coins at once
        coin_ids = ["bitcoin", "ethereum", "solana", "zcash"]
        ids = ",".join(coin_ids)
        
        response = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=aud",
            timeout=10
        )
        response.raise_for_status()
        prices = response.json()
        
        # Map coin IDs to our symbols
        coin_map = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "solana": "SOL",
            "zcash": "ZCASH"
        }
        
        for coin_id, symbol in coin_map.items():
            if coin_id in prices and "aud" in prices[coin_id]:
                data["cryptocurrencies"][symbol] = {
                    "price_aud": prices[coin_id]["aud"],
                    "currency": "AUD"
                }
    except Exception as e:
        print(f"Error fetching crypto prices: {e}")
        data["error"] = str(e)
    
    return data


def fetch_historical_currency_rate(date: str, base: str = "AUD", target: str = "USD") -> Optional[float]:
    """
    Fetch historical exchange rate for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency (default: AUD)
        target: Target currency (default: USD)
        
    Returns:
        Exchange rate or None if not available
    """
    try:
        # Try exchangerate.host API (free, no API key required)
        url = f"https://api.exchangerate.host/{date}"
        params = {"base": base, "symbols": target}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and target in data.get("rates", {}):
            return float(data["rates"][target])
    except Exception as e:
        print(f"Error fetching historical rate for {date}: {e}")
    
    return None


def collect_historical_quarterly_data(start_year: int = 1966, end_year: Optional[int] = None) -> Dict[str, Any]:
    """
    Collect quarterly AUD exchange rate data since modern AUD creation (1966).
    
    Args:
        start_year: Starting year (default: 1966, when modern AUD was introduced)
        end_year: Ending year (None = current year)
        
    Returns:
        Dictionary with quarterly historical data
    """
    from dateutil.relativedelta import relativedelta
    
    if end_year is None:
        end_year = datetime.now().year
    
    historical_data = {
        "collection_date": datetime.now().isoformat(),
        "start_year": start_year,
        "end_year": end_year,
        "frequency": "quarterly",
        "currencies": {
            "USD": [],
            "EUR": [],
            "CNY": []
        }
    }
    
    # Generate quarterly dates
    quarters = []
    current_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    # Start from first quarter (March 31)
    # Adjust to end of quarter dates: Q1=Mar 31, Q2=Jun 30, Q3=Sep 30, Q4=Dec 31
    quarter_ends = [3, 6, 9, 12]  # Month numbers for quarter ends
    
    while current_date <= end_date:
        year = current_date.year
        for month in quarter_ends:
            quarter_date = datetime(year, month, 1)
            # Get last day of month
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            last_day = (next_month - relativedelta(days=1)).day
            quarter_date = datetime(year, month, last_day)
            
            if quarter_date > end_date:
                break
            
            quarters.append(quarter_date.strftime("%Y-%m-%d"))
        
        current_date = datetime(year + 1, 1, 1)
    
    print(f"Collecting historical data for {len(quarters)} quarters from {start_year} to {end_year}...")
    print("This may take a while due to API rate limits...")
    
    # Fetch data for each quarter
    for i, date_str in enumerate(quarters, 1):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(quarters)} quarters...")
        
        for currency in ["USD", "EUR", "CNY"]:
            rate = fetch_historical_currency_rate(date_str, "AUD", currency)
            if rate:
                historical_data["currencies"][currency].append({
                    "date": date_str,
                    "rate": rate
                })
        
        # Small delay to respect API rate limits
        import time
        time.sleep(0.1)
    
    print(f"Historical data collection complete! Collected {len(quarters)} quarters.")
    return historical_data


def collect_all_data() -> Dict[str, Any]:
    """
    Collect all data: currencies, commodities, and cryptocurrencies.
    
    Returns:
        Complete dataset with all tracked assets
    """
    print("Collecting currency rates...")
    currencies = fetch_currency_rates()
    
    print("Collecting commodity prices...")
    commodities = fetch_commodity_prices()
    
    print("Collecting cryptocurrency prices...")
    cryptos = fetch_crypto_prices()
    
    return {
        "collection_date": datetime.now().isoformat(),
        "currencies": currencies,
        "commodities": commodities,
        "cryptocurrencies": cryptos
    }


if __name__ == "__main__":
    # Test the data collection
    print("Testing data collection...")
    data = collect_all_data()
    print("\nCollected Data:")
    print(json.dumps(data, indent=2))

