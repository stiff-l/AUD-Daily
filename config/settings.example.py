"""
Configuration settings for AUD Daily Tracker

Copy this file to settings.py and fill in your actual API keys and settings.
Never commit settings.py to Git (it's in .gitignore)
"""

# API Keys (get these from the respective services)
EXCHANGE_RATE_API_KEY = "your_exchange_rate_api_key_here"
METALS_API_KEY = "your_metals_api_key_here"
CRYPTO_API_KEY = "your_crypto_api_key_here"

# Data Sources Configuration
CURRENCY_SOURCES = {
    "USD": "https://api.exchangerate-api.com/v4/latest/AUD",
    "EUR": "https://api.exchangerate-api.com/v4/latest/AUD",
    "CNY": "https://api.exchangerate-api.com/v4/latest/AUD"
}

COMMODITY_SOURCES = {
    "GOLD": "https://api.metals.live/v1/spot/gold",
    "SILVER": "https://api.metals.live/v1/spot/silver",
    "COPPER": "https://api.metals.live/v1/spot/copper"
}

CRYPTO_SOURCES = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ZCASH": "zcash"
}

# Data Storage Settings
DATA_DIR = "data"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
EXPORT_DIR = "data/exports"

# Update Schedule
UPDATE_FREQUENCY = "daily"  # daily, hourly, etc.

