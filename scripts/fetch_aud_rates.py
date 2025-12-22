#!/usr/bin/env python3
"""
Standalone script to fetch AUD exchange rates using ExchangeRate-API v6.

This script:
- Uses `src.aud_rate_fetcher.AUDRateFetcher`
- Reads the API key and data directories from `config/settings.py`
- Saves JSON/CSV outputs into the same `data/raw` directory structure

You can run it manually:
    python scripts/fetch_aud_rates.py
"""

import os
import sys

# Add project root to path so we can import from src and config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.aud_rate_fetcher import example_run  # noqa: E402


def main() -> None:
    """Main entry point for fetching AUD exchange rates."""
    print("=" * 60)
    print("AUD Exchange Rate Fetcher (ExchangeRate-API v6)")
    print("=" * 60)
    print()

    try:
        example_run()
    except Exception as e:
        # Match project style: simple error output to stdout
        print(f"\nError while fetching AUD rates: {e}")

    print()
    print("=" * 60)
    print("Done")
    print("=" * 60)


if __name__ == "__main__":
    main()


