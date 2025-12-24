"""
RBA Historical Data Importer

Import historical AUD exchange rates from Reserve Bank of Australia (RBA).
Provides daily exchange rate data in Excel files from 1983 onwards.
"""

import sqlite3
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Tuple, Optional
import time
import os
import sys
import re

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import settings
except ImportError:
    # Fallback if config not available
    settings = None

# Import currency history utilities for CSV export
try:
    from .currency_history import load_currency_history_csv
except ImportError:
    try:
        from src.currency_history import load_currency_history_csv
    except ImportError:
        load_currency_history_csv = None

# Configure logging
logger = logging.getLogger(__name__)


class RBAForexImporter:
    """Import historical AUD exchange rates from Reserve Bank of Australia"""
    
    # RBA historical data URLs (daily exchange rates)
    RBA_URLS = [
        "https://www.rba.gov.au/statistics/tables/xls-hist/1983-1986.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/1987-1990.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/1991-1994.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/1995-1998.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/1999-2002.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/2003-2006.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/2007-2009.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/2010-2013.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/2014-2017.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/2018-2022.xls",
        "https://www.rba.gov.au/statistics/tables/xls-hist/2023-current.xls",
    ]
    
    def __init__(self, db_path: str = "data/historical/rba_forex_data.db", download_dir: str = "data/historical/rba_downloads"):
        """
        Initialize the importer
        
        Args:
            db_path: Path to SQLite database file
            download_dir: Directory to store downloaded Excel files
        """
        self.db_path = db_path
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
    def create_database(self):
        """Create SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create exchange rates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                base_currency TEXT NOT NULL,
                quote_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, base_currency, quote_currency, source)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_date 
            ON exchange_rates(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_currency_pair 
            ON exchange_rates(base_currency, quote_currency)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_date_currency 
            ON exchange_rates(date, base_currency, quote_currency)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database created/verified at {self.db_path}")
        
    def download_file(self, url: str) -> Path:
        """
        Download Excel file from RBA
        
        Args:
            url: URL to download from
            
        Returns:
            Path to downloaded file
        """
        filename = url.split('/')[-1]
        filepath = self.download_dir / filename
        
        # Skip if already downloaded
        if filepath.exists():
            logger.info(f"File already exists: {filename}")
            return filepath
        
        try:
            logger.info(f"Downloading {filename}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded {filename}")
            time.sleep(1)  # Be respectful to RBA servers
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            raise
    
    def parse_rba_excel(self, filepath: Path) -> pd.DataFrame:
        """
        Parse RBA Excel file and extract exchange rate data
        
        RBA file structure:
        - Row 1: Currency headers (e.g., "A$1=USD", "A$1=CNY")
        - Rows 2-10: Metadata (Frequency, Type, Units, Source, Publication date, Series ID)
        - Row 11+: Actual data with dates in first column
        
        Args:
            filepath: Path to Excel file
            
        Returns:
            DataFrame with parsed data (dates in first column, rates in other columns)
        """
        try:
            # RBA file structure:
            # Row 0: Title
            # Row 1: Currency headers (e.g., "A$1=USD", "A$1=CNY")
            # Rows 2-10: Metadata (Frequency, Type, Units, Source, Publication date, Series ID)
            # Row 11+: Actual data with dates in first column
            
            # Read with header at row 1, skip rows 2-10 (0-indexed, so rows 2-10)
            # skiprows is applied before header, so we skip rows 2-10 (0-indexed)
            df = pd.read_excel(
                filepath, 
                sheet_name=0, 
                header=1,  # Row 1 (0-indexed) has currency headers
                skiprows=list(range(2, 11))  # Skip rows 2-10 (metadata)
            )
            
            # The first column should be dates - rename it for clarity
            if len(df.columns) > 0:
                first_col_name = df.columns[0]
                # If first column is unnamed or has a date-like name, rename it
                if 'Unnamed' in str(first_col_name) or pd.api.types.is_datetime64_any_dtype(df.iloc[:, 0]):
                    df.rename(columns={first_col_name: 'date'}, inplace=True)
                else:
                    # First column might have a name, but it's still the date column
                    df.rename(columns={first_col_name: 'date'}, inplace=True)
            
            logger.info(f"Parsed {filepath.name} - Shape: {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()[:5]}...")  # Show first 5 columns
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            raise
    
    def normalize_data(self, df: pd.DataFrame, source_file: str) -> List[Tuple]:
        """
        Convert wide-format Excel data to normalized records
        
        Args:
            df: DataFrame with exchange rate data (dates in first column, rates in others)
            source_file: Name of source file for tracking
            
        Returns:
            List of tuples (date, base_currency, quote_currency, rate, source)
        """
        records = []
        
        # First column should be dates (we renamed it to 'date' in parse_rba_excel)
        date_col = 'date' if 'date' in df.columns else df.columns[0]
        
        if date_col is None or len(df.columns) == 0:
            logger.warning(f"Could not identify date column in {source_file}")
            return records
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                date_value = row[date_col]
                
                # Skip invalid dates
                if pd.isna(date_value):
                    continue
                
                # Parse date (handle both datetime objects and strings)
                if isinstance(date_value, str):
                    date = pd.to_datetime(date_value, errors='coerce')
                elif isinstance(date_value, datetime):
                    date = date_value
                else:
                    date = pd.to_datetime(date_value, errors='coerce')
                
                if pd.isna(date):
                    continue
                
                # Format date as YYYY-MM-DD
                date_str = date.strftime('%Y-%m-%d')
                
                # Process each currency column
                for col in df.columns:
                    if col == date_col:
                        continue
                    
                    # Extract currency code from column name
                    # RBA headers are like "A$1=USD" or "Trade-weighted Index May 1970 = 100"
                    currency = self._extract_currency_code(str(col))
                    
                    if not currency:
                        continue
                    
                    rate = row[col]
                    
                    # Skip missing or invalid rates
                    if pd.isna(rate) or rate <= 0:
                        continue
                    
                    # RBA provides rates as AUD per foreign currency (e.g., A$1=USD means 1 AUD = X USD)
                    # We'll store as AUD/XXX (how many XXX for 1 AUD)
                    records.append((
                        date_str,
                        'AUD',
                        currency,
                        float(rate),
                        f'RBA-{source_file}'
                    ))
                    
            except Exception as e:
                logger.debug(f"Skipping row {idx}: {e}")
                continue
        
        logger.info(f"Normalized {len(records)} records from {source_file}")
        return records
    
    def _extract_currency_code(self, column_name: str) -> Optional[str]:
        """
        Extract 3-letter currency code from column name.
        
        RBA headers are typically in format "A$1=USD" or "A$1=CNY"
        Some may be "Trade-weighted Index" which we skip.
        """
        col_lower = column_name.lower().strip()
        
        # Skip trade-weighted index and other non-currency columns
        if 'trade-weighted' in col_lower or 'index' in col_lower:
            return None
        
        # RBA format: "A$1=USD" -> extract "USD"
        # Look for pattern like "=USD" or "=CNY"
        if '=' in column_name:
            parts = column_name.split('=')
            if len(parts) > 1:
                currency_part = parts[-1].strip().upper()
                # Check if it's a 3-letter currency code
                if len(currency_part) == 3 and currency_part.isalpha():
                    return currency_part
        
        # Common currency codes mapping
        currency_map = {
            'usd': 'USD', 'us dollar': 'USD', 'united states': 'USD',
            'eur': 'EUR', 'euro': 'EUR',
            'gbp': 'GBP', 'pound': 'GBP', 'uk': 'GBP', 'sterling': 'GBP', 'ukps': 'GBP',
            'jpy': 'JPY', 'yen': 'JPY', 'japan': 'JPY',
            'cny': 'CNY', 'rmb': 'CNY', 'china': 'CNY', 'yuan': 'CNY', 'cr': 'CNY',
            'cad': 'CAD', 'canada': 'CAD', 'cd': 'CAD',
            'chf': 'CHF', 'swiss': 'CHF', 'switzerland': 'CHF', 'sf': 'CHF',
            'nzd': 'NZD', 'new zealand': 'NZD',
            'sgd': 'SGD', 'singapore': 'SGD', 'sd': 'SGD',
            'hkd': 'HKD', 'hong kong': 'HKD',
            'krw': 'KRW', 'korea': 'KRW', 'korean': 'KRW', 'skw': 'KRW',
            'inr': 'INR', 'india': 'INR', 'rupee': 'INR', 'ire': 'INR',
            'thb': 'THB', 'baht': 'THB', 'thailand': 'THB', 'tb': 'THB',
            'myr': 'MYR', 'ringgit': 'MYR', 'malaysia': 'MYR', 'mr': 'MYR',
            'idr': 'IDR', 'rupiah': 'IDR', 'indonesia': 'IDR', 'ir': 'IDR',
            'twd': 'TWD', 'taiwan': 'TWD', 'ntd': 'TWD',
            'sek': 'SEK', 'krona': 'SEK', 'sweden': 'SEK',
            'nok': 'NOK', 'krone': 'NOK', 'norway': 'NOK',
            'dkk': 'DKK', 'denmark': 'DKK',
            'zar': 'ZAR', 'rand': 'ZAR', 'south africa': 'ZAR', 'sard': 'ZAR',
            'php': 'PHP', 'peso': 'PHP', 'philippines': 'PHP',
            'vnd': 'VND', 'dong': 'VND', 'vietnam': 'VND', 'vd': 'VND',
            'aed': 'AED', 'uae': 'AED', 'uaed': 'AED',
            'pgk': 'PGK', 'png': 'PGK', 'pngk': 'PGK',
            'sdr': 'SDR',  # Special Drawing Rights
        }
        
        # Check for exact matches in currency map
        for key, code in currency_map.items():
            if key in col_lower:
                return code
        
        # Check if it's already a 3-letter code (extract from any part of the string)
        # Look for 3-letter uppercase codes
        matches = re.findall(r'\b[A-Z]{3}\b', column_name.upper())
        if matches:
            # Filter out common non-currency codes
            non_currency = {'RBA', 'AUD', 'IMF', 'WM', 'FXR', 'TWI'}
            for match in matches:
                if match not in non_currency:
                    return match
        
        return None
    
    def insert_records(self, records: List[Tuple]):
        """
        Insert records into database with deduplication
        
        Args:
            records: List of tuples to insert
        """
        if not records:
            logger.warning("No records to insert")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted = 0
        duplicates = 0
        errors = 0
        
        for record in records:
            try:
                cursor.execute("""
                    INSERT INTO exchange_rates 
                    (date, base_currency, quote_currency, rate, source)
                    VALUES (?, ?, ?, ?, ?)
                """, record)
                inserted += 1
            except sqlite3.IntegrityError:
                # Duplicate record, skip
                duplicates += 1
            except Exception as e:
                logger.error(f"Error inserting record {record}: {e}")
                errors += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Inserted: {inserted}, Duplicates: {duplicates}, Errors: {errors}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting RBA FOREX data import...")
        
        # Step 1: Create database
        self.create_database()
        
        # Step 2: Download and process each file
        total_records = 0
        
        for url in self.RBA_URLS:
            try:
                # Download file
                filepath = self.download_file(url)
                
                # Parse Excel file
                df = self.parse_rba_excel(filepath)
                
                # Normalize data
                records = self.normalize_data(df, filepath.name)
                
                # Insert into database
                self.insert_records(records)
                
                total_records += len(records)
                
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
        
        logger.info(f"Import complete! Total records processed: {total_records}")
        self.print_summary()
        
        # Step 3: Export to CSV format
        logger.info("")
        self.export_to_csv()
    
    def print_summary(self):
        """Print summary statistics of imported data"""
        conn = sqlite3.connect(self.db_path)
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
        
        # List of currencies
        cursor.execute("SELECT DISTINCT quote_currency FROM exchange_rates ORDER BY quote_currency")
        currencies = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        logger.info("=" * 60)
        logger.info("DATABASE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records: {total:,}")
        logger.info(f"Date range: {min_date} to {max_date}")
        logger.info(f"Number of currencies: {num_currencies}")
        logger.info(f"Currencies: {', '.join(currencies)}")
        logger.info("=" * 60)
    
    def query_rate(self, date: str, quote_currency: str, base_currency: str = "AUD") -> Optional[float]:
        """
        Query exchange rate from database
        
        Args:
            date: Date in YYYY-MM-DD format
            quote_currency: Quote currency code (e.g., 'USD')
            base_currency: Base currency code (default: 'AUD')
            
        Returns:
            Exchange rate or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rate FROM exchange_rates
            WHERE date = ? AND base_currency = ? AND quote_currency = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (date, base_currency, quote_currency))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_date_range(self, start_date: str, end_date: str, quote_currency: str, 
                      base_currency: str = "AUD") -> pd.DataFrame:
        """
        Get exchange rates for a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            quote_currency: Quote currency code
            base_currency: Base currency code (default: 'AUD')
            
        Returns:
            DataFrame with date and rate columns
        """
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT date, rate FROM exchange_rates
            WHERE date >= ? AND date <= ?
            AND base_currency = ? AND quote_currency = ?
            ORDER BY date
        """
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date, base_currency, quote_currency))
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def export_to_csv(self, csv_path: str = "data/historical/currency_history.csv"):
        """
        Export RBA historical data to CSV format matching existing currency_history.csv format.
        
        Extracts USD, EUR, CNY, SGD rates from SQLite database and saves to CSV.
        Uses batch processing for efficiency.
        
        Args:
            csv_path: Path to the currency history CSV file
        """
        if not load_currency_history_csv:
            logger.warning("currency_history module not available. Skipping CSV export.")
            return
        
        logger.info("Exporting RBA data to CSV format...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all unique dates with rates for target currencies
        target_currencies = ['USD', 'EUR', 'CNY', 'SGD']
        
        # Query all data at once for efficiency
        query = """
            SELECT date, quote_currency, rate 
            FROM exchange_rates
            WHERE base_currency = 'AUD' 
            AND quote_currency IN (?, ?, ?, ?)
            ORDER BY date, quote_currency, created_at DESC
        """
        
        df_db = pd.read_sql_query(query, conn, params=tuple(target_currencies))
        conn.close()
        
        if df_db.empty:
            logger.warning("No data found in database to export")
            return
        
        # Pivot to wide format (one row per date)
        df_pivot = df_db.pivot_table(
            index='date', 
            columns='quote_currency', 
            values='rate', 
            aggfunc='first'  # Take first if duplicates
        ).reset_index()
        
        # Rename columns to match CSV format
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={
            'USD': 'usd_rate',
            'EUR': 'eur_rate',
            'CNY': 'cny_rate',
            'SGD': 'sgd_rate'
        })
        
        # Ensure all required columns exist
        for col in ['usd_rate', 'eur_rate', 'cny_rate', 'sgd_rate']:
            if col not in df_pivot.columns:
                df_pivot[col] = pd.NA
        
        # Convert date to datetime, then to date for consistency
        df_pivot['date'] = pd.to_datetime(df_pivot['date'], errors='coerce').dt.date
        df_pivot['timestamp'] = datetime.now()  # Use current time as import timestamp
        
        # Load existing CSV if it exists and merge
        if os.path.exists(csv_path):
            try:
                df_existing = load_currency_history_csv(csv_path)
                # Ensure date is date type for both
                if 'date' in df_existing.columns:
                    df_existing['date'] = pd.to_datetime(df_existing['date'], errors='coerce').dt.date
                # Combine with new data - RBA data takes precedence
                df_combined = pd.concat([df_existing, df_pivot], ignore_index=True, sort=False)
            except Exception as e:
                logger.warning(f"Could not load existing CSV, creating new one: {e}")
                df_combined = df_pivot
        else:
            df_combined = df_pivot
        
        # Ensure timestamp is datetime
        df_combined['timestamp'] = pd.to_datetime(df_combined['timestamp'], errors='coerce')
        # Ensure date is date type
        df_combined['date'] = pd.to_datetime(df_combined['date'], errors='coerce').dt.date
        
        # Deduplicate by date (keep newest timestamp)
        df_combined = df_combined.sort_values(['date', 'timestamp']).drop_duplicates(subset=['date'], keep='last')
        df_combined = df_combined.sort_values('date').reset_index(drop=True)
        
        # Remove any rows with invalid dates
        df_combined = df_combined.dropna(subset=['date'])
        
        # Ensure required columns in correct order
        required_cols = ['date', 'usd_rate', 'eur_rate', 'cny_rate', 'sgd_rate', 'timestamp']
        df_combined = df_combined[required_cols]
        
        # Save to CSV
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df_combined.to_csv(csv_path, index=False)
        
        exported = len(df_pivot)
        logger.info(f"CSV export complete: {exported} dates exported")
        logger.info(f"CSV saved to: {csv_path}")

