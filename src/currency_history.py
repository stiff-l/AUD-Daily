"""
Currency history utilities.

Handles loading, validation, cleaning, and updating currency history data stored
in CSV form. Supports both daily CSV (`data/processed/currency_daily.csv`) and
historical CSV (`data/historical/currency_history.csv`).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pandas as pd

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


def _coerce_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Convert columns to numeric, coercing errors to NaN."""
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_currency_history_csv(csv_path: str = "data/processed/currency_daily.csv") -> pd.DataFrame:
    """
    Load and validate currency history CSV.

    Returns a cleaned DataFrame with:
    - date: datetime64[ns]
    - numeric rate columns (AUD base)
    - timestamp: datetime64[ns]
    - sorted by date ascending
    - duplicates on date resolved by keeping the most recent timestamp
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Currency history CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Check for required columns (excluding optional ones like jpy_rate for backward compatibility)
    required_core = ["date", "usd_rate", "eur_rate", "cny_rate", "sgd_rate", "timestamp"]
    missing = [c for c in required_core if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in currency CSV: {missing}")
    
    # Add jpy_rate column if it doesn't exist (for backward compatibility)
    if "jpy_rate" not in df.columns:
        df["jpy_rate"] = pd.NA

    # Normalize dates and timestamps
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    rate_cols = ["usd_rate", "eur_rate", "cny_rate", "sgd_rate", "jpy_rate"]
    df = _coerce_numeric(df, rate_cols)

    # Drop rows with invalid dates
    df = df.dropna(subset=["date"])

    # Deduplicate by date, keeping the most recent timestamp
    df = df.sort_values(["date", "timestamp"]).drop_duplicates(subset=["date"], keep="last")

    # Basic sanity: rates should be positive
    for col in rate_cols:
        df.loc[df[col] <= 0, col] = pd.NA

    df = df.sort_values("date").reset_index(drop=True)
    return df


def validate_currency_history(csv_path: str = "data/processed/currency_daily.csv") -> Dict[str, List[str]]:
    """
    Validate the currency history CSV and return any issues found.
    """
    issues: Dict[str, List[str]] = {"errors": [], "warnings": []}

    try:
        df = load_currency_history_csv(csv_path)
    except Exception as exc:  # pylint: disable=broad-except
        issues["errors"].append(str(exc))
        return issues

    # Check for missing values
    rate_cols = ["usd_rate", "eur_rate", "cny_rate", "sgd_rate", "jpy_rate"]
    missing_mask = df[rate_cols].isna()
    for col in rate_cols:
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
    timestamp = timestamp or datetime.now(timezone.utc)

    # Load existing (or create new DataFrame)
    if os.path.exists(csv_path):
        df = load_currency_history_csv(csv_path)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Round rates to 3 decimal places for currency_daily.csv
    round_to_3 = csv_path.endswith("currency_daily.csv")
    
    def round_rate(rate):
        """Round rate to 3 decimal places if not None."""
        if rate is not None:
            return round(float(rate), 3)
        return pd.NA
    
    new_row = {
        "date": pd.to_datetime(date).date(),
        "usd_rate": round_rate(usd_rate) if round_to_3 else (float(usd_rate) if usd_rate is not None else pd.NA),
        "eur_rate": round_rate(eur_rate) if round_to_3 else (float(eur_rate) if eur_rate is not None else pd.NA),
        "cny_rate": round_rate(cny_rate) if round_to_3 else (float(cny_rate) if cny_rate is not None else pd.NA),
        "sgd_rate": round_rate(sgd_rate) if round_to_3 else (float(sgd_rate) if sgd_rate is not None else pd.NA),
        "jpy_rate": round_rate(jpy_rate) if round_to_3 else (float(jpy_rate) if jpy_rate is not None else pd.NA),
        "timestamp": pd.to_datetime(timestamp),
    }

    # Create new row DataFrame with compatible dtypes
    # If df is empty, create with explicit structure; otherwise match existing dtypes
    if df.empty:
        new_df = pd.DataFrame([new_row])
        df = new_df
    else:
        # Create new DataFrame with same dtypes as existing df to avoid concat warnings
        new_df = pd.DataFrame([new_row])
        # Align dtypes to match existing DataFrame
        for col in df.columns:
            if col in new_df.columns and col in df.columns:
                new_df[col] = new_df[col].astype(df[col].dtype, errors="ignore")
        
        # Append and deduplicate by date (keep newest timestamp)
        # Use pd.concat with sort=False to avoid FutureWarning
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
    
    # Round existing rates to 3 decimal places for currency_daily.csv
    if round_to_3:
        rate_cols = ["usd_rate", "eur_rate", "cny_rate", "sgd_rate", "jpy_rate"]
        for col in rate_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: round(x, 3) if pd.notna(x) and isinstance(x, (int, float)) else x)
    
    # Save back to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    return df

