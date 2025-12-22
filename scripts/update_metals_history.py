#!/usr/bin/env python3
"""
Fetch latest metals prices and upsert into data/processed/metals_history.csv.

Relies on:
- METALS_API_KEY (optional, better quality)
- EXCHANGE_RATE_API_KEY (from config/settings.py) to convert USD -> AUD
"""

import os
import sys
from datetime import datetime
from typing import Dict, Tuple

import requests

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from config import settings
except ImportError:
    from config import settings_example as settings

from src.metals_history import upsert_metals_history_row


def fetch_aud_usd_rate() -> float:
    """Fetch AUD->USD rate using exchangerate-api (same as existing pipeline)."""
    resp = requests.get("https://api.exchangerate-api.com/v4/latest/AUD", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    rate = data.get("rates", {}).get("USD")
    if not rate:
        raise RuntimeError("AUD->USD rate not found in response")
    return float(rate)


def fetch_metals_spot_usd(api_key: str | None) -> Dict[str, float]:
    """
    Fetch spot prices in USD for key metals.

    Prefer metals-api.com when API key is provided; fallback to metals.live free feed.
    Returns mapping of metal -> price_usd.
    """
    metals_map = {
        "gold": "XAU",
        "silver": "XAG",
        "platinum": "XPT",
        "palladium": "XPD",
    }

    prices: Dict[str, float] = {}

    if api_key and api_key != "your_metals_api_key_here":
        # metals-api.com supports batch symbols via /latest
        symbols = ",".join(metals_map.values())
        url = f"https://metals-api.com/api/latest?access_key={api_key}&base=USD&symbols={symbols}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        for metal, code in metals_map.items():
            price = rates.get(code)
            if price:
                prices[metal] = float(price)

    # Fallback to metals.live if any missing
    for metal in metals_map:
        if metal in prices:
            continue
        try:
            resp = requests.get(f"https://api.metals.live/v1/spot/{metal}", timeout=10)
            resp.raise_for_status()
            payload = resp.json()
            price = None
            # metals.live often returns list like [[timestamp, price]]
            if isinstance(payload, list) and payload:
                first = payload[0]
                if isinstance(first, (list, tuple)) and len(first) >= 2:
                    price = first[1]
                elif isinstance(first, (int, float)):
                    price = first
            elif isinstance(payload, dict):
                price = payload.get("price") or payload.get("spot") or payload.get("value")
            if price:
                prices[metal] = float(price)
        except Exception:
            continue

    if not prices:
        raise RuntimeError("Failed to fetch metals spot prices from all sources")

    return prices


def main() -> None:
    api_key = getattr(settings, "METALS_API_KEY", None)
    csv_path = getattr(settings, "PROCESSED_DATA_DIR", "data/processed")
    csv_path = os.path.join(csv_path, "metals_history.csv")

    usd_rate = fetch_aud_usd_rate()
    spot_usd = fetch_metals_spot_usd(api_key)

    # Convert USD -> AUD (AUD price = USD price / rate where rate= AUD->USD)
    def to_aud(price_usd: float) -> float:
        return price_usd / usd_rate if usd_rate else price_usd

    gold = to_aud(spot_usd.get("gold"))
    silver = to_aud(spot_usd.get("silver"))
    platinum = to_aud(spot_usd.get("platinum"))
    palladium = to_aud(spot_usd.get("palladium"))

    now = datetime.utcnow()
    upsert_metals_history_row(
        csv_path=csv_path,
        date=now.date(),
        gold_aud=gold,
        silver_aud=silver,
        platinum_aud=platinum,
        palladium_aud=palladium,
        timestamp=now,
    )

    print("✓ Metals history updated")
    print(f"  Source: {'metals-api.com' if api_key and api_key != 'your_metals_api_key_here' else 'metals.live (fallback)'}")
    print(f"  Saved: {csv_path}")


if __name__ == "__main__":
    main()

