"""
Commodity history utilities.

Handles loading, validation, cleaning, and updating commodity history data stored
in CSV form. Supports daily CSV (`data/commodities_data/processed/commodity_daily.csv`).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List

import pandas as pd

# Expected CSV columns
REQUIRED_COLUMNS: tuple = (
    "date",
    "gold_price",
    "silver_price",
    "copper_price",
    "aluminium_price",
    "zinc_price",
    "nickel_price",
    "timestamp",
)


def _coerce_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Convert columns to numeric, coercing errors to NaN."""
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


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
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Commodity history CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Check for required columns
    required_core = ["date", "gold_price", "silver_price", "copper_price", "aluminium_price", "zinc_price", "nickel_price", "timestamp"]
    missing = [c for c in required_core if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in commodity CSV: {missing}")

    # Normalize dates and timestamps
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    price_cols = ["gold_price", "silver_price", "copper_price", "aluminium_price", "zinc_price", "nickel_price"]
    df = _coerce_numeric(df, price_cols)

    # Drop rows with invalid dates
    df = df.dropna(subset=["date"])

    # Deduplicate by date, keeping the most recent timestamp
    df = df.sort_values(["date", "timestamp"]).drop_duplicates(subset=["date"], keep="last")

    # Basic sanity: prices should be positive
    for col in price_cols:
        df.loc[df[col] <= 0, col] = pd.NA

    df = df.sort_values("date").reset_index(drop=True)
    return df


def validate_commodity_history(csv_path: str = "data/commodities_data/processed/commodity_daily.csv") -> Dict[str, List[str]]:
    """
    Validate the commodity history CSV and return any issues found.
    """
    issues: Dict[str, List[str]] = {"errors": [], "warnings": []}

    try:
        df = load_commodity_history_csv(csv_path)
    except Exception as exc:  # pylint: disable=broad-except
        issues["errors"].append(str(exc))
        return issues

    # Check for missing values
    price_cols = ["gold_price", "silver_price", "copper_price", "aluminium_price", "zinc_price", "nickel_price"]
    missing_mask = df[price_cols].isna()
    for col in price_cols:
        missing_rows = df.index[missing_mask[col]].tolist()
        if missing_rows:
            issues["warnings"].append(f"{col} has missing/invalid values at rows: {missing_rows}")

    # Check for gaps in dates (not fatal)
    if len(df["date"].unique()) > 1:
        date_series = pd.to_datetime(df["date"])
        expected_range = pd.date_range(date_series.min(), date_series.max(), freq="D")
        missing_dates = expected_range.difference(date_series)
        if not missing_dates.empty:
            issues["warnings"].append(
                f"Missing {len(missing_dates)} date(s): {', '.join(d.strftime('%Y-%m-%d') for d in missing_dates[:10])}"
                + ("..." if len(missing_dates) > 10 else "")
            )

    return issues


def upsert_commodity_history_row(
    csv_path: str,
    date: datetime,
    gold_price: float | None = None,
    silver_price: float | None = None,
    copper_price: float | None = None,
    aluminium_price: float | None = None,
    zinc_price: float | None = None,
    nickel_price: float | None = None,
    timestamp: datetime | None = None,
) -> pd.DataFrame:
    """
    Insert or update a commodity row for a given date, returning the new DataFrame.
    """
    timestamp = timestamp or datetime.now(timezone.utc)

    # Load existing (or create new DataFrame)
    if os.path.exists(csv_path):
        df = load_commodity_history_csv(csv_path)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    new_row = {
        "date": pd.to_datetime(date).date(),
        "gold_price": float(gold_price) if gold_price is not None else pd.NA,
        "silver_price": float(silver_price) if silver_price is not None else pd.NA,
        "copper_price": float(copper_price) if copper_price is not None else pd.NA,
        "aluminium_price": float(aluminium_price) if aluminium_price is not None else pd.NA,
        "zinc_price": float(zinc_price) if zinc_price is not None else pd.NA,
        "nickel_price": float(nickel_price) if nickel_price is not None else pd.NA,
        "timestamp": pd.to_datetime(timestamp),
    }

    # Create new row DataFrame with compatible dtypes
    if df.empty:
        new_df = pd.DataFrame([new_row])
        df = new_df
    else:
        new_df = pd.DataFrame([new_row])
        # Align dtypes to match existing DataFrame
        for col in df.columns:
            if col in new_df.columns and col in df.columns:
                new_df[col] = new_df[col].astype(df[col].dtype, errors="ignore")
        
        # Append and deduplicate by date (keep newest timestamp)
        # Suppress FutureWarning about empty/all-NA concatenation
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            df = pd.concat([df, new_df], ignore_index=True, sort=False)
    
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.sort_values(["date", "timestamp"]).drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)

    # Ensure all required columns are present and in the correct order
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    
    # Reorder columns to match REQUIRED_COLUMNS
    df = df[list(REQUIRED_COLUMNS)]
    
    # Save back to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    return df
