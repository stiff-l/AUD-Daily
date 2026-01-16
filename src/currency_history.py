"""
Currency history utilities.

Handles loading, validation, cleaning, and updating currency history data stored
in CSV form. Supports both daily CSV (`data/forex_data/processed/currency_daily.csv`) and
historical CSV (`data/forex_data/historical/currency_history.csv`).
"""

from __future__ import annotations

import os
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Import base history utilities
try:
    from .base_history import (
        load_history_csv_generic,
        validate_history_generic,
        upsert_history_row_generic
    )
except ImportError:
    from src.base_history import (
        load_history_csv_generic,
        validate_history_generic,
        upsert_history_row_generic
    )

# Expected CSV columns
REQUIRED_COLUMNS: Tuple[str, ...] = (
    "date",
    "usd_rate",
    "eur_rate",
    "cny_rate",
    "sgd_rate",
    "jpy_rate",
    "timestamp",
)

# Data columns (rates)
RATE_COLS = ["usd_rate", "eur_rate", "cny_rate", "sgd_rate", "jpy_rate"]


def load_currency_history_csv(csv_path: str = "data/forex_data/processed/currency_daily.csv") -> pd.DataFrame:
    """
    Load and validate currency history CSV.

    Returns a cleaned DataFrame with:
    - date: datetime64[ns]
    - numeric rate columns (AUD base)
    - timestamp: datetime64[ns]
    - sorted by date ascending
    - duplicates on date resolved by keeping the most recent timestamp
    """
    required_core = ["date", "usd_rate", "eur_rate", "cny_rate", "sgd_rate", "timestamp"]
    optional_columns = {"jpy_rate": pd.NA}  # Optional for backward compatibility
    
    return load_history_csv_generic(
        csv_path=csv_path,
        required_columns=REQUIRED_COLUMNS,
        data_columns=RATE_COLS,
        optional_columns=optional_columns,
        error_name="Currency"
    )


def validate_currency_history(csv_path: str = "data/forex_data/processed/currency_daily.csv") -> Dict[str, List[str]]:
    """
    Validate the currency history CSV and return any issues found.
    """
    return validate_history_generic(
        csv_path=csv_path,
        load_func=load_currency_history_csv,
        data_columns=RATE_COLS,
        error_name="Currency"
    )


def upsert_currency_history_row(
    csv_path: str,
    date: datetime,
    usd_rate: float | None = None,
    eur_rate: float | None = None,
    cny_rate: float | None = None,
    sgd_rate: float | None = None,
    jpy_rate: float | None = None,
    timestamp: datetime | None = None,
) -> pd.DataFrame:
    """
    Insert or update a currency row for a given date, returning the new DataFrame.
    """
    # Round rates to 3 decimal places for currency_daily.csv
    round_to_3 = csv_path.endswith("currency_daily.csv")
    
    def round_rate(csv_path_param, rate):
        """Round rate to 3 decimal places if not None and if round_to_3."""
        if rate is not None:
            if round_to_3:
                return round(float(rate), 3)
            return float(rate)
        return pd.NA
    
    new_row_data = {
        "usd_rate": usd_rate,
        "eur_rate": eur_rate,
        "cny_rate": cny_rate,
        "sgd_rate": sgd_rate,
        "jpy_rate": jpy_rate,
        "timestamp": timestamp or datetime.now(timezone.utc),
    }
    
    return upsert_history_row_generic(
        csv_path=csv_path,
        date=date,
        required_columns=REQUIRED_COLUMNS,
        new_row_data=new_row_data,
        load_func=load_currency_history_csv,
        round_func=round_rate if round_to_3 else None
    )

