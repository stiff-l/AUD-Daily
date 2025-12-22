#!/usr/bin/env python3
"""
Generate Charts Script

Create visualizations from AUD tracking data.
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.visualizations import (
        load_historical_data,
        plot_currency_trends,
        plot_crypto_trends,
        plot_commodity_trends,
        plot_all_trends,
        plot_comparison_chart,
        HAS_VIS_LIBS
    )
except ImportError as e:
    print(f"Error importing visualization module: {e}")
    print("Make sure matplotlib and seaborn are installed:")
    print("  pip install matplotlib seaborn pandas")
    sys.exit(1)


def ensure_output_dir(output_dir: str = "data/exports") -> None:
    """Create output directory if it doesn't exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Generate charts from AUD Daily Tracker data"
    )
    parser.add_argument(
        "--type",
        choices=["currencies", "crypto", "commodities", "all", "comparison", "dashboard"],
        default="dashboard",
        help="Type of chart to generate (default: dashboard)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days to include (default: all available)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: auto-generated in data/exports/)"
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        help="Specific assets to plot (for comparison chart)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display chart instead of saving (requires GUI)"
    )
    
    args = parser.parse_args()
    
    if not HAS_VIS_LIBS:
        print("Error: Visualization libraries not installed")
        print("Install with: pip install matplotlib seaborn pandas")
        sys.exit(1)
    
    # Load historical data
    try:
        print(f"Loading historical data...")
        df = load_historical_data(days=args.days)
        print(f"Loaded {len(df['date'].unique())} days of data")
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Make sure you have data files in data/processed/")
        print("Run: python scripts/daily_update.py to collect data first")
        sys.exit(1)
    
    # Determine output path
    output_path = args.output
    if not output_path and not args.show:
        ensure_output_dir()
        date_str = df["date"].max().strftime("%Y%m%d")
        chart_type = args.type.replace("comparison", "compare")
        output_path = f"data/exports/chart_{chart_type}_{date_str}.png"
    
    # Generate chart
    try:
        if args.type == "currencies":
            plot_currency_trends(df, output_path if not args.show else None)
        elif args.type == "crypto":
            plot_crypto_trends(df, output_path if not args.show else None)
        elif args.type == "commodities":
            plot_commodity_trends(df, output_path if not args.show else None)
        elif args.type == "dashboard" or args.type == "all":
            plot_all_trends(df, output_path if not args.show else None)
        elif args.type == "comparison":
            if not args.assets:
                print("Error: --assets required for comparison chart")
                print("Example: --assets USD EUR BTC ETH")
                sys.exit(1)
            plot_comparison_chart(df, args.assets, output_path if not args.show else None)
        
        if not args.show:
            print(f"\n✓ Chart generated successfully!")
            print(f"  Saved to: {output_path}")
        else:
            print("\n✓ Chart displayed")
            
    except Exception as e:
        print(f"Error generating chart: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

