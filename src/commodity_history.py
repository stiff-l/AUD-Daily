"""
Commodity history utilities.

Handles loading, validation, cleaning, and updating commodity history data stored
in CSV form. Supports daily CSV (`data/commodities_data/processed/commodity_daily.csv`).
"""

from __future__ import annotations

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
    "gold_price",
    "silver_price",
    "copper_price",
    "aluminium_price",
    "nickel_price",
    "timestamp",
)

# Data columns (prices)
PRICE_COLS = ["gold_price", "silver_price", "copper_price", "aluminium_price", "nickel_price"]


def load_commodity_history_csv(csv_path: str = "data/commodities_data/processed/commodity_daily.csv") -> pd.DataFrame:
    """
    Load and validate commodity history CSV.

    Returns a cleaned DataFrame with:
    - date: datetime64[ns]
    - numeric price columns (AUD prices)
    - timestamp: datetime64[ns]
    - sorted by date ascending
    - duplicates on date resolved by keeping the most recent timestamp
    """
    return load_history_csv_generic(
        csv_path=csv_path,
        required_columns=REQUIRED_COLUMNS,
        data_columns=PRICE_COLS,
        optional_columns=None,
        error_name="Commodity"
    )


def validate_commodity_history(csv_path: str = "data/commodities_data/processed/commodity_daily.csv") -> Dict[str, List[str]]:
    """
    Validate the commodity history CSV and return any issues found.
    """
    return validate_history_generic(
        csv_path=csv_path,
        load_func=load_commodity_history_csv,
        data_columns=PRICE_COLS,
        error_name="Commodity"
    )


def upsert_commodity_history_row(
    csv_path: str,
    date: datetime,
    gold_price: float | None = None,
    silver_price: float | None = None,
    copper_price: float | None = None,
    aluminium_price: float | None = None,
    nickel_price: float | None = None,
    timestamp: datetime | None = None,
) -> pd.DataFrame:
    """
    Insert or update a commodity row for a given date, returning the new DataFrame.
    """
    new_row_data = {
        "gold_price": gold_price,
        "silver_price": silver_price,
        "copper_price": copper_price,
        "aluminium_price": aluminium_price,
        "nickel_price": nickel_price,
        "timestamp": timestamp or datetime.now(timezone.utc),
    }
    
    return upsert_history_row_generic(
        csv_path=csv_path,
        date=date,
        required_columns=REQUIRED_COLUMNS,
        new_row_data=new_row_data,
        load_func=load_commodity_history_csv,
        round_func=None
    )
