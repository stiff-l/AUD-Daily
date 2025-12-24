#!/usr/bin/env python3
"""
Query RBA Historical Data

Query the SQLite database and CSV file containing RBA historical exchange rate data.
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rba_historical_importer import RBAForexImporter
from src.currency_history import load_currency_history_csv
import pandas as pd


def query_rate(importer, date, currency):
    """Query a specific exchange rate"""
    rate = importer.query_rate(date, currency)
    if rate:
        print(f"AUD/{currency} on {date}: {rate:.4f}")
    else:
        print(f"No data found for AUD/{currency} on {date}")


def query_date_range(importer, start_date, end_date, currency):
    """Query exchange rates for a date range"""
    df = importer.get_date_range(start_date, end_date, currency)
    if df.empty:
        print(f"No data found for AUD/{currency} from {start_date} to {end_date}")
    else:
        print(f"\nAUD/{currency} rates from {start_date} to {end_date}:")
        print(f"Total records: {len(df)}")
        print(f"\nFirst 10 records:")
        print(df.head(10).to_string(index=False))
        if len(df) > 10:
            print(f"\n... ({len(df) - 10} more records)")
            print(f"\nLast 5 records:")
            print(df.tail(5).to_string(index=False))
        print(f"\nStatistics:")
        print(f"  Min: {df['rate'].min():.4f}")
        print(f"  Max: {df['rate'].max():.4f}")
        print(f"  Mean: {df['rate'].mean():.4f}")
        print(f"  Latest: {df.iloc[-1]['rate']:.4f} on {df.iloc[-1]['date'].strftime('%Y-%m-%d')}")


def list_currencies(importer):
    """List all available currencies in the database"""
    import sqlite3
    conn = sqlite3.connect(importer.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT quote_currency 
        FROM exchange_rates 
        ORDER BY quote_currency
    """)
    currencies = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"\nAvailable currencies ({len(currencies)}):")
    print(", ".join(currencies))


def show_database_summary(importer):
    """Show database summary statistics"""
    import sqlite3
    conn = sqlite3.connect(importer.db_path)
    cursor = conn.cursor()
    
    # Total records
    cursor.execute("SELECT COUNT(*) FROM exchange_rates")
    total = cursor.fetchone()[0]
    
    # Date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM exchange_rates")
    min_date, max_date = cursor.fetchone()
    
    # Currencies
    cursor.execute("SELECT COUNT(DISTINCT quote_currency) FROM exchange_rates")
    num_currencies = cursor.fetchone()[0]
    
    # Dates
    cursor.execute("SELECT COUNT(DISTINCT date) FROM exchange_rates")
    num_dates = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)
    print(f"Total records: {total:,}")
    print(f"Unique dates: {num_dates:,}")
    print(f"Date range: {min_date} to {max_date}")
    print(f"Number of currencies: {num_currencies}")
    print("=" * 60)


def query_csv(date=None, start_date=None, end_date=None, csv_type="daily"):
    """Query the CSV file
    
    Args:
        date: Single date to query
        start_date: Start date for range query
        end_date: End date for range query
        csv_type: "daily" for daily CSV, "historical" for historical CSV
    """
    if csv_type == "historical":
        csv_path = "data/historical/currency_history.csv"
    else:
        csv_path = "data/processed/currency_daily.csv"
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    
    df = load_currency_history_csv(csv_path)
    
    if date:
        # Single date
        date_obj = pd.to_datetime(date).date()
        row = df[df['date'] == date_obj]
        if row.empty:
            print(f"No data found for {date}")
        else:
            row = row.iloc[0]
            print(f"\nExchange rates on {date}:")
            print(f"  USD: {row['usd_rate']:.4f}" if pd.notna(row['usd_rate']) else "  USD: N/A")
            print(f"  EUR: {row['eur_rate']:.4f}" if pd.notna(row['eur_rate']) else "  EUR: N/A")
            print(f"  CNY: {row['cny_rate']:.4f}" if pd.notna(row['cny_rate']) else "  CNY: N/A")
            print(f"  SGD: {row['sgd_rate']:.4f}" if pd.notna(row['sgd_rate']) else "  SGD: N/A")
    
    elif start_date and end_date:
        # Date range
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()
        filtered = df[(df['date'] >= start) & (df['date'] <= end)]
        
        if filtered.empty:
            print(f"No data found from {start_date} to {end_date}")
        else:
            print(f"\nExchange rates from {start_date} to {end_date}:")
            print(f"Total records: {len(filtered)}")
            print(f"\nFirst 10 records:")
            print(filtered.head(10)[['date', 'usd_rate', 'eur_rate', 'cny_rate', 'sgd_rate']].to_string(index=False))
            if len(filtered) > 10:
                print(f"\n... ({len(filtered) - 10} more records)")
                print(f"\nLast 5 records:")
                print(filtered.tail(5)[['date', 'usd_rate', 'eur_rate', 'cny_rate', 'sgd_rate']].to_string(index=False))
    else:
        # Show summary
        print(f"\nCSV File Summary:")
        print(f"  Total rows: {len(df):,}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  USD rates: {df['usd_rate'].notna().sum():,}")
        print(f"  EUR rates: {df['eur_rate'].notna().sum():,}")
        print(f"  CNY rates: {df['cny_rate'].notna().sum():,}")
        print(f"  SGD rates: {df['sgd_rate'].notna().sum():,}")


def main():
    parser = argparse.ArgumentParser(
        description="Query RBA historical exchange rate data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query a specific rate
  python scripts/query_rba_data.py --rate 2023-01-01 USD
  
  # Query a date range
  python scripts/query_rba_data.py --range 2023-01-01 2023-12-31 USD
  
  # List all currencies
  python scripts/query_rba_data.py --list-currencies
  
  # Show database summary
  python scripts/query_rba_data.py --summary
  
  # Query CSV file
  python scripts/query_rba_data.py --csv-date 2023-01-01
  python scripts/query_rba_data.py --csv-range 2023-01-01 2023-12-31
        """
    )
    
    parser.add_argument("--rate", nargs=2, metavar=("DATE", "CURRENCY"),
                       help="Query specific rate (e.g., --rate 2023-01-01 USD)")
    parser.add_argument("--range", nargs=3, metavar=("START", "END", "CURRENCY"),
                       help="Query date range (e.g., --range 2023-01-01 2023-12-31 USD)")
    parser.add_argument("--list-currencies", action="store_true",
                       help="List all available currencies")
    parser.add_argument("--summary", action="store_true",
                       help="Show database summary")
    parser.add_argument("--csv-date", type=str,
                       help="Query daily CSV for specific date (YYYY-MM-DD)")
    parser.add_argument("--csv-range", nargs=2, metavar=("START", "END"),
                       help="Query daily CSV for date range")
    parser.add_argument("--csv-summary", action="store_true",
                       help="Show daily CSV file summary")
    parser.add_argument("--historical-csv-date", type=str,
                       help="Query historical CSV for specific date (YYYY-MM-DD)")
    parser.add_argument("--historical-csv-range", nargs=2, metavar=("START", "END"),
                       help="Query historical CSV for date range")
    parser.add_argument("--historical-csv-summary", action="store_true",
                       help="Show historical CSV file summary")
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = RBAForexImporter()
    
    # Handle CSV queries
    if args.csv_date:
        query_csv(date=args.csv_date, csv_type="daily")
    elif args.csv_range:
        query_csv(start_date=args.csv_range[0], end_date=args.csv_range[1], csv_type="daily")
    elif args.csv_summary:
        query_csv(csv_type="daily")
    elif args.historical_csv_date:
        query_csv(date=args.historical_csv_date, csv_type="historical")
    elif args.historical_csv_range:
        query_csv(start_date=args.historical_csv_range[0], end_date=args.historical_csv_range[1], csv_type="historical")
    elif args.historical_csv_summary:
        query_csv(csv_type="historical")
    # Handle database queries
    elif args.rate:
        date, currency = args.rate
        query_rate(importer, date, currency.upper())
    elif args.range:
        start_date, end_date, currency = args.range
        query_date_range(importer, start_date, end_date, currency.upper())
    elif args.list_currencies:
        list_currencies(importer)
    elif args.summary:
        show_database_summary(importer)
    else:
        # Default: show summary
        show_database_summary(importer)
        print()
        query_csv(csv_type="daily")


if __name__ == "__main__":
    main()

