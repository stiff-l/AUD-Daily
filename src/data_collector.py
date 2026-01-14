"""
Data Collector Module

This module handles fetching currency exchange rates from APIs.
Tracks: USD, EUR, CNY, SGD, JPY against AUD.
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
    Fetch AUD exchange rates against major currencies (USD, EUR, CNY, SGD, JPY).
    
    Returns:
        Dictionary with currency rates and metadata
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "currencies": {}
    }
    
    # Using a free API (exchangerate-api.com)
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/AUD", timeout=10)
        response.raise_for_status()
        rates = response.json()
        
        # Extract the currencies we care about: USD, EUR, CNY, SGD, JPY
        for currency in ["USD", "EUR", "CNY", "SGD", "JPY"]:
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
    # Try frankfurter.app API (free, no API key required, supports historical data)
    try:
        url = f"https://api.frankfurter.app/{date}"
        params = {"base": base, "symbols": target}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "rates" in data and target in data.get("rates", {}):
            return float(data["rates"][target])
    except Exception as e:
        # Fallback to exchangerate.host if frankfurter fails
        try:
            url = f"https://api.exchangerate.host/{date}"
            params = {"base": base, "symbols": target}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and target in data.get("rates", {}):
                return float(data["rates"][target])
        except Exception as e2:
            print(f"Error fetching historical rate for {date}: {e2}")
    
    return None


def collect_historical_data_for_date(date: str) -> Dict[str, Any]:
    """
    Collect historical currency data for a specific date.
    Fetches all tracked currencies: USD, EUR, CNY, SGD, JPY.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Dictionary with currency rates and metadata (similar to collect_all_data format)
    """
    currencies_data = {
        "timestamp": datetime.now().isoformat(),
        "currencies": {}
    }
    
    # Fetch all tracked currencies for the historical date
    currencies_to_fetch = ["USD", "EUR", "CNY", "SGD", "JPY"]
    
    for currency in currencies_to_fetch:
        rate = fetch_historical_currency_rate(date, "AUD", currency)
        if rate:
            currencies_data["currencies"][currency] = {
                "rate": rate,
                "base": "AUD",
                "date": date
            }
        else:
            print(f"Warning: Could not fetch {currency} rate for {date}")
    
    # Return in same format as collect_all_data
    return {
        "collection_date": datetime.now().isoformat(),
        "currencies": currencies_data
    }


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
    Collect currency data only (USD, EUR, CNY, SGD, JPY).
    
    Returns:
        Dataset with currency rates
    """
    print("Collecting currency rates...")
    currencies = fetch_currency_rates()
    
    return {
        "collection_date": datetime.now().isoformat(),
        "currencies": currencies
    }


if __name__ == "__main__":
    # Test the data collection
    print("Testing data collection...")
    data = collect_all_data()
    print("\nCollected Data:")
    print(json.dumps(data, indent=2))

