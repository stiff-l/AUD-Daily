"""
AUD Exchange Rate Data Fetcher

Fetches current and recent historical AUD exchange rates from ExchangeRate-API.

This module is integrated with the existing AUD Daily project:
- Reads API key and data directories from `config.settings`
- Uses the same directory conventions as `data_storage.py`
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import pandas as pd
import requests

# Add parent directory to path to import config, mirroring `data_collector.py`
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import settings
except ImportError:
    # Fallback to example settings if real settings are not present
    from config import settings_example as settings


class AUDRateFetcher:
    """
    Fetch AUD exchange rates using ExchangeRate-API v6.

    This class expects a valid `EXCHANGE_RATE_API_KEY` to be set in `config/settings.py`.
    """

    def __init__(self) -> None:
        api_key: Optional[str] = getattr(settings, "EXCHANGE_RATE_API_KEY", None)

        # Treat placeholder value as "not configured"
        if not api_key or api_key == "your_exchange_rate_api_key_here":
            raise ValueError(
                "EXCHANGE_RATE_API_KEY is not configured.\n"
                "Please set a valid key in config/settings.py "
                "(EXCHANGE_RATE_API_KEY = 'your_real_key')."
            )

        self.api_key: str = api_key
        self.base_url: str = f"https://v6.exchangerate-api.com/v6/{self.api_key}"
        self.base_currency: str = "AUD"

        # Use configured directories where available
        self.raw_dir: str = getattr(settings, "RAW_DATA_DIR", "data/raw")

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{path}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error fetching rates from {url}: {e}")

        data = resp.json()
        if data.get("result") != "success":
            raise RuntimeError(f"API Error from {url}: {data.get('error-type', 'Unknown error')}")
        return data

    def fetch_latest_rates(self, target_currencies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch latest AUD exchange rates.

        Args:
            target_currencies: List of currencies to fetch (e.g., ['USD', 'EUR', 'GBP']).
                               If None, fetches all available currencies.

        Returns:
            dict: Exchange rate data with timestamp and filtered rates.
        """
        data = self._get(f"latest/{self.base_currency}")

        now = datetime.now()
        rates: Dict[str, Any] = {
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "base": data.get("base_code", self.base_currency),
            "rates": data.get("conversion_rates", {}),
        }

        if target_currencies:
            filtered: Dict[str, float] = {}
            for curr in target_currencies:
                if curr in rates["rates"]:
                    filtered[curr] = rates["rates"][curr]
            rates["rates"] = filtered

        return rates

    def fetch_historical_rate(self, date: datetime | str, target_currency: str = "USD") -> Dict[str, Any]:
        """
        Fetch historical AUD exchange rate for a specific date.

        Args:
            date: Date string in format 'YYYY-MM-DD' or datetime object.
            target_currency: Currency to get rate for (default: 'USD').

        Returns:
            dict: Historical rate data with base, target, and date.
        """
        if isinstance(date, datetime):
            date_str_api = date.strftime("%Y/%m/%d")
            date_str_out = date.strftime("%Y-%m-%d")
        else:
            # Convert YYYY-MM-DD to YYYY/MM/DD for API
            date_str_out = date
            date_str_api = date.replace("-", "/")

        data = self._get(f"history/{self.base_currency}/{date_str_api}")

        return {
            "date": date_str_out,
            "base": data.get("base_code", self.base_currency),
            "rate": data.get("conversion_rates", {}).get(target_currency),
            "currency": target_currency,
        }

    def fetch_week_history(self, target_currency: str = "USD") -> pd.DataFrame:
        """
        Fetch last 7 days of AUD exchange rates for a single currency.

        Args:
            target_currency: Currency to track (default: 'USD').

        Returns:
            pandas.DataFrame: Historical rates for the week, sorted by date.
        """
        history: List[Dict[str, Any]] = []

        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            try:
                rate_data = self.fetch_historical_rate(date, target_currency)
                history.append(rate_data)
            except Exception as e:
                # Match existing project style: print warnings instead of raising
                print(
                    f"Warning: Could not fetch data for {date.strftime('%Y-%m-%d')}: {e}"
                )

        df = pd.DataFrame(history)
        if not df.empty:
            df = df.sort_values("date").reset_index(drop=True)
        return df

    def save_to_json(self, data: Dict[str, Any], filename: str) -> str:
        """
        Save data to a JSON file in the configured raw data directory.
        """
        os.makedirs(self.raw_dir, exist_ok=True)
        filepath = os.path.join(self.raw_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Data saved to {filepath}")
        return filepath

    def save_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        Save a DataFrame to CSV in the configured raw data directory.
        """
        os.makedirs(self.raw_dir, exist_ok=True)
        filepath = os.path.join(self.raw_dir, filename)

        df.to_csv(filepath, index=False)
        print(f"✅ Data saved to {filepath}")
        return filepath


def example_run() -> None:
    """
    Example usage of `AUDRateFetcher`.

    This function is used by the standalone script in `scripts/`,
    but can also be run directly for quick manual testing.
    """
    fetcher = AUDRateFetcher()

    # Define currencies you want to track
    currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "NZD", "SGD"]

    print("🔄 Fetching latest AUD exchange rates...")

    # Fetch latest rates
    latest = fetcher.fetch_latest_rates(currencies)
    print(f"\n📊 Latest rates (as of {latest['date']}):")
    for curr, rate in latest["rates"].items():
        try:
            print(f"  AUD → {curr}: {float(rate):.4f}")
        except (TypeError, ValueError):
            print(f"  AUD → {curr}: {rate}")

    # Save latest rates
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fetcher.save_to_json(latest, f"aud_rates_latest_{timestamp}.json")

    # Fetch weekly history for USD
    print("\n🔄 Fetching 7-day history for AUD/USD...")
    weekly_df = fetcher.fetch_week_history("USD")
    print("\n📈 Weekly AUD/USD rates:")
    print(weekly_df)

    # Calculate daily change
    if not weekly_df.empty and len(weekly_df) > 1:
        weekly_df["daily_change"] = weekly_df["rate"].diff()
        weekly_df["daily_change_pct"] = (
            weekly_df["rate"].pct_change() * 100
        ).round(2)

    # Save weekly data
    fetcher.save_to_csv(
        weekly_df,
        f"aud_usd_weekly_{datetime.now().strftime('%Y%m%d')}.csv",
    )

    print("\n✨ Data fetching complete!")


if __name__ == "__main__":
    example_run()


