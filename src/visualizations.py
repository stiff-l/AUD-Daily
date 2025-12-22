"""
Visualization Module

Create charts and graphs from AUD tracking data using matplotlib and seaborn.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    import pandas as pd
    import numpy as np
    HAS_VIS_LIBS = True
except ImportError:
    HAS_VIS_LIBS = False
    print("Warning: matplotlib/seaborn not installed. Install with: pip install matplotlib seaborn")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_storage import load_data
from src.data_formatter import standardize_data
from src.metals_history import load_metals_history_csv


def load_historical_data(
    data_dir: str = "data/processed",
    days: Optional[int] = None,
    metals_csv_path: str = "data/processed/metals_history.csv",
) -> pd.DataFrame:
    """
    Load historical data from multiple JSON files into a pandas DataFrame.
    
    Args:
        data_dir: Directory containing JSON files
        days: Number of days to load (None = all available)
        
    Returns:
        DataFrame with historical data
    """
    if not HAS_VIS_LIBS:
        raise ImportError("matplotlib and pandas are required for visualizations")
    
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Find all JSON files
    json_files = sorted(Path(data_dir).glob("aud_daily_*.json"), reverse=True)
    
    if not json_files:
        raise ValueError("No data files found")
    
    # Limit to requested number of days
    if days:
        json_files = json_files[:days]
    
    # Load and process each file
    records = []
    for filepath in json_files:
        data = load_data(str(filepath))
        if data:
            standardized = standardize_data(data)
            date = standardized.get("date")

            if not date:
                continue

            # Extract currencies
            for symbol, info in standardized.get("currencies", {}).items():
                records.append(
                    {
                        "date": date,
                        "type": "currency",
                        "asset": symbol,
                        "value": info.get("rate"),
                        "currency": "AUD",
                    }
                )

            # Extract commodities
            for symbol, info in standardized.get("commodities", {}).items():
                price_aud = info.get("price_aud")
                if price_aud:  # Only include if price is available
                    records.append(
                        {
                            "date": date,
                            "type": "commodity",
                            "asset": symbol,
                            "value": price_aud,
                            "currency": "AUD",
                            "unit": info.get("unit"),
                        }
                    )

            # Extract cryptocurrencies
            for symbol, info in standardized.get("cryptocurrencies", {}).items():
                records.append(
                    {
                        "date": date,
                        "type": "cryptocurrency",
                        "asset": symbol,
                        "value": info.get("price_aud"),
                        "currency": "AUD",
                    }
                )

    # Optionally merge metals CSV (gold/silver/platinum/palladium)
    try:
        metals_df = load_metals_history_csv(metals_csv_path)
        if not metals_df.empty:
            for _, row in metals_df.iterrows():
                date_val = row["date"]
                assets = {
                    "GOLD": row.get("gold_aud"),
                    "SILVER": row.get("silver_aud"),
                    "PLATINUM": row.get("platinum_aud"),
                    "PALLADIUM": row.get("palladium_aud"),
                }
                for asset, value in assets.items():
                    if pd.notna(value):
                        records.append(
                            {
                                "date": date_val,
                                "type": "commodity",
                                "asset": asset,
                                "value": value,
                                "currency": "AUD",
                                "unit": "oz",
                            }
                        )
    except FileNotFoundError:
        # Metals CSV optional; ignore if missing
        pass
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    if df.empty:
        raise ValueError("No data records found")
    
    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    return df


def plot_currency_trends(df: pd.DataFrame, output_path: Optional[str] = None, 
                         figsize: Tuple[int, int] = (12, 6)) -> None:
    """
    Plot currency exchange rate trends over time.
    
    Args:
        df: DataFrame with historical data
        output_path: Path to save the plot (None = display)
        figsize: Figure size (width, height)
    """
    if not HAS_VIS_LIBS:
        raise ImportError("matplotlib is required")
    
    currency_df = df[df["type"] == "currency"].copy()
    
    if currency_df.empty:
        print("No currency data available for plotting")
        return
    
    plt.figure(figsize=figsize)
    
    for currency in sorted(currency_df["asset"].unique()):
        currency_data = currency_df[currency_df["asset"] == currency]
        plt.plot(currency_data["date"], currency_data["value"], 
                marker="o", label=currency, linewidth=2, markersize=4)
    
    plt.title("AUD Exchange Rates Over Time", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Exchange Rate (AUD Base)", fontsize=12)
    plt.legend(title="Currencies", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Format x-axis dates (only if multiple dates)
    if len(currency_df["date"].unique()) > 1:
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(currency_df["date"].unique()) // 10)))
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Chart saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_crypto_trends(df: pd.DataFrame, output_path: Optional[str] = None,
                       figsize: Tuple[int, int] = (12, 6)) -> None:
    """
    Plot cryptocurrency price trends over time.
    
    Args:
        df: DataFrame with historical data
        output_path: Path to save the plot (None = display)
        figsize: Figure size (width, height)
    """
    if not HAS_VIS_LIBS:
        raise ImportError("matplotlib is required")
    
    crypto_df = df[df["type"] == "cryptocurrency"].copy()
    
    if crypto_df.empty:
        print("No cryptocurrency data available for plotting")
        return
    
    plt.figure(figsize=figsize)
    
    for crypto in sorted(crypto_df["asset"].unique()):
        crypto_data = crypto_df[crypto_df["asset"] == crypto]
        plt.plot(crypto_data["date"], crypto_data["value"], 
                marker="o", label=crypto, linewidth=2, markersize=4)
    
    plt.title("Cryptocurrency Prices (AUD) Over Time", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Price (AUD)", fontsize=12)
    plt.legend(title="Cryptocurrencies", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.yscale("log")  # Use log scale for crypto prices
    plt.tight_layout()
    
    # Format x-axis dates (only if multiple dates)
    if len(crypto_df["date"].unique()) > 1:
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(crypto_df["date"].unique()) // 10)))
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Chart saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_commodity_trends(df: pd.DataFrame, output_path: Optional[str] = None,
                          figsize: Tuple[int, int] = (12, 6)) -> None:
    """
    Plot commodity price trends over time.
    
    Args:
        df: DataFrame with historical data
        output_path: Path to save the plot (None = display)
        figsize: Figure size (width, height)
    """
    if not HAS_VIS_LIBS:
        raise ImportError("matplotlib is required")
    
    commodity_df = df[df["type"] == "commodity"].copy()
    
    if commodity_df.empty:
        print("No commodity data available for plotting")
        return
    
    plt.figure(figsize=figsize)
    
    for commodity in sorted(commodity_df["asset"].unique()):
        commodity_data = commodity_df[commodity_df["asset"] == commodity]
        plt.plot(commodity_data["date"], commodity_data["value"], 
                marker="o", label=commodity, linewidth=2, markersize=4)
    
    plt.title("Commodity Prices (AUD) Over Time", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Price (AUD)", fontsize=12)
    plt.legend(title="Commodities", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Format x-axis dates (only if multiple dates)
    if len(commodity_df["date"].unique()) > 1:
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(commodity_df["date"].unique()) // 10)))
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Chart saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_all_trends(df: pd.DataFrame, output_path: Optional[str] = None,
                   figsize: Tuple[int, int] = (15, 10)) -> None:
    """
    Create a comprehensive dashboard with all trends.
    
    Args:
        df: DataFrame with historical data
        output_path: Path to save the plot (None = display)
        figsize: Figure size (width, height)
    """
    if not HAS_VIS_LIBS:
        raise ImportError("matplotlib is required")
    
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle("AUD Daily Tracker - Comprehensive Dashboard", 
                fontsize=18, fontweight="bold", y=0.995)
    
    # 1. Currency trends
    ax1 = axes[0, 0]
    currency_df = df[df["type"] == "currency"].copy()
    if not currency_df.empty:
        for currency in sorted(currency_df["asset"].unique()):
            currency_data = currency_df[currency_df["asset"] == currency]
            ax1.plot(currency_data["date"], currency_data["value"], 
                    marker="o", label=currency, linewidth=2, markersize=3)
        ax1.set_title("Currency Exchange Rates", fontweight="bold")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Rate (AUD Base)")
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # 2. Crypto trends
    ax2 = axes[0, 1]
    crypto_df = df[df["type"] == "cryptocurrency"].copy()
    if not crypto_df.empty:
        for crypto in sorted(crypto_df["asset"].unique()):
            crypto_data = crypto_df[crypto_df["asset"] == crypto]
            ax2.plot(crypto_data["date"], crypto_data["value"], 
                    marker="o", label=crypto, linewidth=2, markersize=3)
        ax2.set_title("Cryptocurrency Prices", fontweight="bold")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Price (AUD)")
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        ax2.set_yscale("log")
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # 3. Commodity trends
    ax3 = axes[1, 0]
    commodity_df = df[df["type"] == "commodity"].copy()
    if not commodity_df.empty:
        for commodity in sorted(commodity_df["asset"].unique()):
            commodity_data = commodity_df[commodity_df["asset"] == commodity]
            ax3.plot(commodity_data["date"], commodity_data["value"], 
                    marker="o", label=commodity, linewidth=2, markersize=3)
        ax3.set_title("Commodity Prices", fontweight="bold")
        ax3.set_xlabel("Date")
        ax3.set_ylabel("Price (AUD)")
        ax3.legend(fontsize=8)
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # 4. Summary statistics
    ax4 = axes[1, 1]
    ax4.axis("off")
    
    # Calculate summary stats
    summary_text = ["Summary Statistics\n" + "="*30 + "\n"]
    
    if not currency_df.empty:
        summary_text.append("Currencies:")
        for currency in sorted(currency_df["asset"].unique()):
            currency_data = currency_df[currency_df["asset"] == currency]
            latest = currency_data["value"].iloc[-1]
            change = ((latest - currency_data["value"].iloc[0]) / currency_data["value"].iloc[0] * 100) if len(currency_data) > 1 else 0
            summary_text.append(f"  {currency}: {latest:.4f} ({change:+.2f}%)")
        summary_text.append("")
    
    if not crypto_df.empty:
        summary_text.append("Cryptocurrencies:")
        for crypto in sorted(crypto_df["asset"].unique()):
            crypto_data = crypto_df[crypto_df["asset"] == crypto]
            latest = crypto_data["value"].iloc[-1]
            change = ((latest - crypto_data["value"].iloc[0]) / crypto_data["value"].iloc[0] * 100) if len(crypto_data) > 1 else 0
            summary_text.append(f"  {crypto}: ${latest:,.2f} ({change:+.2f}%)")
    
    ax4.text(0.1, 0.5, "\n".join(summary_text), 
            fontsize=10, family="monospace", verticalalignment="center")
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Dashboard saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_comparison_chart(df: pd.DataFrame, assets: List[str], 
                         output_path: Optional[str] = None,
                         figsize: Tuple[int, int] = (12, 6)) -> None:
    """
    Compare multiple assets on the same chart (normalized to percentage change).
    
    Args:
        df: DataFrame with historical data
        assets: List of asset symbols to compare
        output_path: Path to save the plot (None = display)
        figsize: Figure size (width, height)
    """
    if not HAS_VIS_LIBS:
        raise ImportError("matplotlib is required")
    
    plt.figure(figsize=figsize)
    
    for asset in assets:
        asset_data = df[df["asset"] == asset].copy()
        if not asset_data.empty:
            # Normalize to percentage change from first value
            first_value = asset_data["value"].iloc[0]
            if first_value and first_value != 0:
                asset_data["pct_change"] = ((asset_data["value"] - first_value) / first_value) * 100
                plt.plot(asset_data["date"], asset_data["pct_change"], 
                        marker="o", label=asset, linewidth=2, markersize=4)
    
    plt.title("Asset Comparison - Percentage Change Over Time", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Percentage Change (%)", fontsize=12)
    plt.legend(title="Assets", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color="black", linestyle="--", linewidth=1)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Format x-axis dates (only if multiple dates)
    asset_dates = df[df["asset"].isin(assets)]["date"].unique()
    if len(asset_dates) > 1:
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(asset_dates) // 10)))
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Chart saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()

