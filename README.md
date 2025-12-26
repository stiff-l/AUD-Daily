# AUD Daily Tracker

A project to track the Australian Dollar (AUD) daily against:
- **Major Currencies**: USD, EUR, CNY, SGD, JPY
First ship the above. 

In the future we will integrate:
- **Commodities**: Gold, Silver, Copper
- **Cryptocurrencies**: BTC, ETH, SOL, ZCASH

## Features

- **Automated Daily Collection**: Runs at 5pm Cairns time (COB) via scheduled task
- **Data Storage**: Saves raw and processed data in JSON format
- **Historical Tracking**: Maintains daily records in CSV format

## Project Structure

```
AUD-Daily/
├── README.md                 # This file - project overview
├── LICENSE                   # License information
├── .gitignore                # Files to ignore in Git
├── requirements.txt          # Python dependencies
├── config/                   # Configuration files
│   └── settings.py           # API keys
├── src/                      # Source code
│   ├── data_collector.py     # Fetch currency data from APIs
│   ├── data_formatter.py     # Format and standardize data
│   ├── data_storage.py       # Save data to files and CSV tables
│   └── currency_history.py  # CSV table management for historical data
├── data/                     # Data storage
│   ├── raw/                  # Raw data files (timestamped JSON)
│   ├── processed/            # Processed data (date-based JSON + CSV tables)
├── scripts/                  # Utility scripts
│   ├── daily_update.py       # Manual data collection
│   ├── scheduled_update.py   # Scheduled update (5pm Cairns time)
│   ├── view_data.py          # View collected data
│   └── standardize_existing_data.py  # Convert old data formats
└── docs/                     # Documentation
    ├── DATA_FORMATTING_GUIDE.md  # Data format and viewing guide
    └── SCHEDULING_GUIDE.md       # Scheduling setup guide
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

3. **Set up configuration** (optional):
   - Copy `config/settings.example.py` to `config/settings.py`
   - API keys are optional - the system works with free APIs by default

4. **Test data collection**:
   ```bash
   python scripts/daily_update.py
   ```

5. **Set up scheduled updates**:
   - See `docs/SCHEDULING_GUIDE.md` for detailed instructions
   - Schedule `scripts/scheduled_update.py` to run at 5pm Cairns time (AEST)

## Data Sources

- **Currency rates**: exchangerate-api.com (free, no API key required)
  - Tracks: USD, EUR, CNY, SGD, JPY against AUD

## Scheduling

The script is designed to run at **5pm Cairns time (AEST - UTC+10)** daily. Use:
- **macOS/Linux**: cron job

See `docs/SCHEDULING_GUIDE.md` for scheduling examples.

## Viewing Data

Use the `view_data.py` script to view collected data:

```bash
# View latest data
python scripts/view_data.py

# View specific date
python scripts/view_data.py --date 2025-12-22

# Different formats
python scripts/view_data.py --format summary
python scripts/view_data.py --format json
```

## Data Storage

The system saves data in multiple formats:

**Daily Updates (Automatically updated):**
1. **Raw JSON** (`data/raw/`) - Original API responses with timestamps
2. **Processed JSON** (`data/processed/aud_daily_*.json`) - Standardized daily data files
3. **Daily CSV** (`data/processed/currency_daily.csv`) - Daily updated table with one row per day

**Historical (Static - manually updated):**
1. **Historical Database** (`data/historical/rba_forex_data.db`) - RBA historical SQLite database
2. **Historical CSV** (`data/historical/currency_history.csv`) - Historical CSV exported from RBA database

Each day's data includes:
- Date and timestamp
- Exchange rates for USD, EUR, CNY, SGD, JPY
- Base currency (AUD)

## Documentation

- `docs/DATA_FORMATTING_GUIDE.md` - Data format and viewing guide
- `docs/SCHEDULING_GUIDE.md` - How to schedule daily updates

