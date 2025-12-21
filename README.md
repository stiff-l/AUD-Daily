# AUD Daily Tracker

A project to track the Australian Dollar (AUD) daily against:
- **Major Currencies**: USD, EUR, CNY
- **Commodities**: Gold, Silver, Copper
- **Cryptocurrencies**: BTC, ETH, SOL, ZCASH

## Project Structure

```
AUD-Daily/
├── README.md                 # This file - project overview
├── LICENSE                 # License information
├── .gitignore               # Files to ignore in Git
├── requirements.txt         # Python dependencies (if using Python)
├── config/                  # Configuration files
│   └── settings.py          # API keys, settings
├── src/                     # Source code
│   ├── __init__.py
│   ├── data_collector.py    # Fetch data from APIs
│   ├── data_processor.py    # Process and clean data
│   └── data_storage.py      # Save data to files/database
├── data/                    # Data storage
│   ├── raw/                 # Raw data files
│   ├── processed/           # Processed/cleaned data
│   └── exports/             # Exported reports
├── notebooks/               # Jupyter notebooks for analysis
│   └── analysis.ipynb       # Data analysis notebook
├── scripts/                 # Utility scripts
│   └── daily_update.py      # Script to run daily updates
├── docs/                    # Documentation
│   └── project-description.md
└── tests/                   # Test files
    └── test_data_collector.py
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**:
   - Copy `config/settings.example.py` to `config/settings.py`
   - Add your API keys (if needed for data sources)

4. **Run the data collector**:
   ```bash
   python scripts/daily_update.py
   ```

## Data Sources

You'll need to decide on data sources for:
- **Currency rates**: Free APIs like exchangerate-api.com, fixer.io, or currencylayer.com
- **Commodity prices**: APIs like metals-api.com, or financial data providers
- **Cryptocurrency prices**: APIs like CoinGecko, CoinMarketCap, or CryptoCompare

## Next Steps

1. Choose your data sources and get API keys if needed
2. Implement the data collection scripts
3. Set up automated daily data collection (cron job or scheduled task)
4. Create analysis and visualization tools

## Learning Resources

- [Python for Beginners](https://www.python.org/about/gettingstarted/)
- [Working with APIs in Python](https://realpython.com/python-api/)
- [Pandas for Data Analysis](https://pandas.pydata.org/docs/getting_started/intro_tutorials/)

