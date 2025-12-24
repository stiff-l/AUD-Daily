#!/usr/bin/env python3
"""
RBA Historical Data Import Script

Import historical AUD exchange rates from Reserve Bank of Australia (RBA).
Downloads Excel files from RBA and stores data in SQLite database.

Usage:
    python scripts/import_rba_historical.py
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rba_historical_importer import RBAForexImporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run RBA historical data import"""
    print("=" * 60)
    print("RBA Historical Data Importer")
    print("Importing AUD exchange rates from Reserve Bank of Australia")
    print("=" * 60)
    print()
    
    try:
        # Initialize importer
        # Database will be stored in data/historical/rba_forex_data.db
        # Downloaded Excel files will be stored in data/historical/rba_downloads/
        importer = RBAForexImporter(
            db_path="data/historical/rba_forex_data.db",
            download_dir="data/historical/rba_downloads"
        )
        
        # Run import
        importer.run()
        
        print("\n" + "=" * 60)
        print("Import complete!")
        print("=" * 60)
        print(f"SQLite database: {importer.db_path}")
        print(f"CSV file: data/historical/currency_history.csv")
        print(f"Downloaded files: {importer.download_dir}")
        print()
        print("Data has been saved to:")
        print("  - SQLite database (all currencies)")
        print("  - CSV file (USD, EUR, CNY, SGD) in existing format")
        print()
        print("You can query the database using:")
        print("  from src.rba_historical_importer import RBAForexImporter")
        print("  importer = RBAForexImporter()")
        print("  rate = importer.query_rate('2023-01-01', 'USD')")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

