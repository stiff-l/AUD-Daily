# RBA Historical Data Query Guide

This guide shows you how to view and query the RBA historical exchange rate data.

## Quick Start

### View Database Summary
```bash
python scripts/query_rba_data.py --summary
```

### List All Available Currencies
```bash
python scripts/query_rba_data.py --list-currencies
```

## Querying the SQLite Database

The SQLite database (`data/historical/rba_forex_data.db`) contains **all currencies** from RBA (35 currencies total).

### Query a Specific Rate
```bash
# Query USD rate for a specific date
python scripts/query_rba_data.py --rate 2023-01-03 USD

# Query EUR rate
python scripts/query_rba_data.py --rate 2023-01-03 EUR

# Query CNY rate
python scripts/query_rba_data.py --rate 2023-01-03 CNY
```

### Query a Date Range
```bash
# Get all USD rates for January 2023
python scripts/query_rba_data.py --range 2023-01-01 2023-01-31 USD

# Get EUR rates for a year
python scripts/query_rba_data.py --range 2023-01-01 2023-12-31 EUR
```

## Querying the CSV Files

There are two CSV files available:

1. **Daily CSV** (`data/processed/currency_daily.csv`) - Updated daily by `daily_update.py` and `scheduled_update.py`
2. **Historical CSV** (`data/historical/currency_history.csv`) - Static historical data exported from RBA database

Both contain **USD, EUR, CNY, SGD** in the standard format.

### Query Daily CSV

```bash
# Get all 4 currencies for a specific date
python scripts/query_rba_data.py --csv-date 2023-01-03

# Get all currencies for a date range
python scripts/query_rba_data.py --csv-range 2023-01-01 2023-01-31

# Show daily CSV summary
python scripts/query_rba_data.py --csv-summary
```

### Query Historical CSV

```bash
# Get all 4 currencies for a specific date
python scripts/query_rba_data.py --historical-csv-date 2023-01-03

# Get all currencies for a date range
python scripts/query_rba_data.py --historical-csv-range 2023-01-01 2023-01-31

# Show historical CSV summary
python scripts/query_rba_data.py --historical-csv-summary
```

## Using Python Directly

You can also query the data programmatically in Python:

### Query SQLite Database
```python
from src.rba_historical_importer import RBAForexImporter

importer = RBAForexImporter()

# Get a specific rate
rate = importer.query_rate('2023-01-03', 'USD')
print(f"USD rate: {rate}")

# Get a date range
df = importer.get_date_range('2023-01-01', '2023-01-31', 'USD')
print(df)
```

### Query CSV Files
```python
from src.currency_history import load_currency_history_csv
import pandas as pd

# Load the daily CSV
df_daily = load_currency_history_csv('data/processed/currency_daily.csv')

# Load the historical CSV
df_historical = load_currency_history_csv('data/historical/currency_history.csv')

# Filter by date
date = pd.to_datetime('2023-01-03').date()
row = df_daily[df_daily['date'] == date]
print(row)

# Filter by date range
start = pd.to_datetime('2023-01-01').date()
end = pd.to_datetime('2023-01-31').date()
filtered = df_daily[(df_daily['date'] >= start) & (df_daily['date'] <= end)]
print(filtered)
```

## Available Currencies

The database contains 35 currencies:
- **Major**: USD, EUR, GBP, JPY, CNY, SGD, CAD, CHF, NZD, HKD
- **Asian**: KRW, INR, THB, MYR, IDR, TWD, VND, PHP
- **Others**: AED, ZAR, SEK, NOK, DKK, SDR, PGK, SAR
- **Historical**: ATS, BEF, DEM, ESP, FIM, FRF, GRD, IEP, ITL, NLG, PTE

## Data Coverage

- **Date Range**: 1983-12-12 to 2025-12-24 (42+ years)
- **Total Records**: 198,602
- **Unique Dates**: 10,590
- **CSV Coverage**:
  - USD: 10,589 dates (99.99%)
  - EUR: 6,773 dates (EUR introduced later)
  - CNY: 10,581 dates (99.9%)
  - SGD: 10,587 dates (99.97%)

## Notes

- Exchange rates are quoted as **AUD per foreign currency** (e.g., AUD/USD = 0.68 means 1 AUD = 0.68 USD)
- Data is available for business days only (no weekends/holidays)
- Some currencies may not have data for all dates (especially historical currencies)

