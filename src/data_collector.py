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
from typing import Dict, Any
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
    
    Returns:
        Dictionary with commodity prices and metadata
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "commodities": {}
    }
    
    # Note: You'll need to implement this based on your chosen API
    # This is a placeholder structure
    commodities = ["GOLD", "SILVER", "COPPER"]
    
    for commodity in commodities:
        # TODO: Implement actual API call based on your data source
        data["commodities"][commodity] = {
            "price": None,
            "currency": "USD",
            "unit": "oz" if commodity in ["GOLD", "SILVER"] else "lb"
        }
    
    print("Warning: Commodity price fetching not yet implemented.")
    print("You'll need to add API calls based on your chosen data source.")
    
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

