"""
Base History Module

Generic history functions that can be used by both currency and commodity history modules.
"""

from __future__ import annotations

import os
import warnings
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Callable

import pandas as pd


def _coerce_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Convert columns to numeric, coercing errors to NaN."""
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_history_csv_generic(
    csv_path: str,
    required_columns: List[str],
    data_columns: List[str],
    optional_columns: Optional[Dict[str, any]] = None,
    error_name: str = "History"
) -> pd.DataFrame:
    """
    Load and validate history CSV with generic column handling.
    
    Args:
        csv_path: Path to the CSV file
        required_columns: List of required column names (including date, timestamp)
        data_columns: List of data columns (rates or prices) to validate
        optional_columns: Dict of optional columns to add if missing (column_name: default_value)
        error_name: Name to use in error messages (e.g., "Currency" or "Commodity")
        
    Returns:
        Cleaned DataFrame with normalized dates, timestamps, and numeric data columns
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{error_name} history CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Check for required core columns (excluding optional ones)
    required_core = [col for col in required_columns if col not in (optional_columns or {}).keys()]
    missing = [c for c in required_core if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {error_name.lower()} CSV: {missing}")
    
    # Add optional columns if they don't exist
    if optional_columns:
        for col_name, default_value in optional_columns.items():
            if col_name not in df.columns:
                df[col_name] = default_value

    # Normalize dates and timestamps
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Coerce data columns to numeric
    df = _coerce_numeric(df, data_columns)

    # Drop rows with invalid dates
    df = df.dropna(subset=["date"])

    # Deduplicate by date, keeping the most recent timestamp
    df = df.sort_values(["date", "timestamp"]).drop_duplicates(subset=["date"], keep="last")

    # Basic sanity: data values should be positive
    for col in data_columns:
        if col in df.columns:
            df.loc[df[col] <= 0, col] = pd.NA

    df = df.sort_values("date").reset_index(drop=True)
    return df


def validate_history_generic(
    csv_path: str,
    load_func: Callable[[str], pd.DataFrame],
    data_columns: List[str],
    error_name: str = "History"
) -> Dict[str, List[str]]:
    """
    Validate the history CSV and return any issues found.
    
    Args:
        csv_path: Path to the CSV file
        load_func: Function to load the CSV (should return a DataFrame)
        data_columns: List of data columns to check for missing values
        error_name: Name to use in error messages
        
    Returns:
        Dictionary with "errors" and "warnings" lists
    """
    issues: Dict[str, List[str]] = {"errors": [], "warnings": []}

    try:
        df = load_func(csv_path)
    except Exception as exc:  # pylint: disable=broad-except
        issues["errors"].append(str(exc))
        return issues

    # Check for missing values
    missing_mask = df[data_columns].isna()
    for col in data_columns:
        if col in df.columns:
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


def upsert_history_row_generic(
    csv_path: str,
    date: datetime,
    required_columns: Tuple[str, ...],
    new_row_data: Dict[str, any],
    load_func: Callable[[str], pd.DataFrame],
    round_func: Optional[Callable[[str, any], any]] = None,
) -> pd.DataFrame:
    """
    Insert or update a history row for a given date, returning the new DataFrame.
    
    Args:
        csv_path: Path to the CSV file
        date: Date for the row
        required_columns: Tuple of required column names in order
        new_row_data: Dictionary of column_name: value pairs for the new row
        load_func: Function to load existing CSV
        round_func: Optional function to round values (csv_path, value) -> rounded_value
        
    Returns:
        Updated DataFrame
    """
    timestamp = datetime.now(timezone.utc)
    if "timestamp" in new_row_data and new_row_data["timestamp"]:
        timestamp = new_row_data["timestamp"]

    # Load existing (or create new DataFrame)
    if os.path.exists(csv_path):
        df = load_func(csv_path)
    else:
        df = pd.DataFrame(columns=required_columns)

    # Prepare new row with date and timestamp
    new_row = {
        "date": pd.to_datetime(date).date(),
        "timestamp": pd.to_datetime(timestamp),
    }
    
    # Add data columns, applying rounding if specified
    for col, value in new_row_data.items():
        if col == "timestamp":
            continue
        if round_func:
            new_row[col] = round_func(csv_path, value)
        else:
            new_row[col] = float(value) if value is not None else pd.NA

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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            df = pd.concat([df, new_df], ignore_index=True, sort=False)
    
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.sort_values(["date", "timestamp"]).drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)

    # Ensure all required columns are present and in the correct order
    for col in required_columns:
        if col not in df.columns:
            df[col] = pd.NA
    
    # Reorder columns to match REQUIRED_COLUMNS
    df = df[list(required_columns)]
    
    # Apply rounding to existing rows if specified
    if round_func:
        for col in new_row_data.keys():
            if col != "timestamp" and col in df.columns:
                df[col] = df[col].apply(
                    lambda x: round_func(csv_path, x) if pd.notna(x) and isinstance(x, (int, float)) else x
                )
    
    # Save back to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    return df
