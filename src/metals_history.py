"""
Metals history utilities.

Handles loading, validation, cleaning, and updating metals history data stored
in CSV form (`data/processed/metals_history.csv`).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd

# Expected CSV columns
REQUIRED_COLUMNS: Tuple[str, ...] = (
    "date",
    "gold_aud",
    "silver_aud",
    "platinum_aud",
    "palladium_aud",
    "timestamp",
)


def _coerce_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Convert columns to numeric, coercing errors to NaN."""
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_metals_history_csv(csv_path: str = "data/processed/metals_history.csv") -> pd.DataFrame:
    """
    Load and validate metals history CSV.

    Returns a cleaned DataFrame with:
    - date: datetime64[ns]
    - numeric price columns in AUD
    - timestamp: datetime64[ns]
    - sorted by date ascending
    - duplicates on date resolved by keeping the most recent timestamp
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metals history CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in metals CSV: {missing}")

    # Normalize dates and timestamps
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    price_cols = ["gold_aud", "silver_aud", "platinum_aud", "palladium_aud"]
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


def validate_metals_history(csv_path: str = "data/processed/metals_history.csv") -> Dict[str, List[str]]:
    """
    Validate the metals history CSV and return any issues found.
    """
    issues: Dict[str, List[str]] = {"errors": [], "warnings": []}

    try:
        df = load_metals_history_csv(csv_path)
    except Exception as exc:  # pylint: disable=broad-except
        issues["errors"].append(str(exc))
        return issues

    # Check for missing values
    price_cols = ["gold_aud", "silver_aud", "platinum_aud", "palladium_aud"]
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


def upsert_metals_history_row(
    csv_path: str,
    date: datetime,
    gold_aud: float,
    silver_aud: float,
    platinum_aud: float,
    palladium_aud: float,
    timestamp: datetime | None = None,
) -> pd.DataFrame:
    """
    Insert or update a metals row for a given date, returning the new DataFrame.
    """
    timestamp = timestamp or datetime.utcnow()

    # Load existing (or create new DataFrame)
    if os.path.exists(csv_path):
        df = load_metals_history_csv(csv_path)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    new_row = {
        "date": pd.to_datetime(date).date(),
        "gold_aud": float(gold_aud),
        "silver_aud": float(silver_aud),
        "platinum_aud": float(platinum_aud),
        "palladium_aud": float(palladium_aud),
        "timestamp": pd.to_datetime(timestamp),
    }

    # Append and deduplicate by date (keep newest timestamp)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.sort_values(["date", "timestamp"]).drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)

    # Save back to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    return df

