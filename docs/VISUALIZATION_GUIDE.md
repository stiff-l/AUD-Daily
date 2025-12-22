# Visualization Guide

This guide explains how to create charts and visualizations from your AUD Daily Tracker data.

## Quick Start

Generate a comprehensive dashboard with all your data:
```bash
python scripts/generate_charts.py --type dashboard
```

This creates a chart saved to `data/exports/chart_dashboard_YYYYMMDD.png`

## Installation

Visualization libraries are included in `requirements.txt`:
```bash
pip install matplotlib seaborn pandas
```

They should already be installed if you followed the setup guide.

## Chart Types

### 1. Dashboard (All-in-One)
Comprehensive view with all data types:
```bash
python scripts/generate_charts.py --type dashboard
```

Shows:
- Currency exchange rates
- Cryptocurrency prices
- Commodity prices
- Summary statistics

### 2. Currency Trends
Track AUD exchange rates over time:
```bash
python scripts/generate_charts.py --type currencies
```

### 3. Cryptocurrency Trends
View crypto price movements:
```bash
python scripts/generate_charts.py --type crypto
```

Uses logarithmic scale for better visualization of price ranges.

### 4. Commodity Trends
Track commodity prices (requires API key):
```bash
python scripts/generate_charts.py --type commodities
```

### 5. Comparison Chart
Compare multiple assets on one chart (normalized to percentage change):
```bash
python scripts/generate_charts.py --type comparison --assets USD EUR BTC ETH
```

This shows how different assets have moved relative to each other.

## Options

### Limit Days
Show only recent data:
```bash
python scripts/generate_charts.py --type dashboard --days 30
```

### Custom Output Location
```bash
python scripts/generate_charts.py --type dashboard --output reports/my_report.png
```

### Display Instead of Save
Show chart in a window (requires GUI):
```bash
python scripts/generate_charts.py --type dashboard --show
```

## Examples

### Daily Report Generation
Create a daily dashboard automatically:
```bash
# Add to your daily_update.py or cron job
python scripts/daily_update.py
python scripts/generate_charts.py --type dashboard
```

### Weekly Summary
Generate a 7-day trend chart:
```bash
python scripts/generate_charts.py --type dashboard --days 7 --output weekly_summary.png
```

### Currency Analysis
Focus on currency movements:
```bash
python scripts/generate_charts.py --type currencies --days 30 --output currency_trends.png
```

### Crypto vs Traditional Assets
Compare cryptocurrencies with currencies:
```bash
python scripts/generate_charts.py --type comparison --assets USD EUR BTC ETH SOL
```

## Programmatic Usage

You can also use the visualization module in your own scripts:

```python
from src.visualizations import load_historical_data, plot_currency_trends

# Load data
df = load_historical_data(days=30)

# Generate chart
plot_currency_trends(df, output_path="my_chart.png")
```

## Customization

Edit `src/visualizations.py` to customize:
- Chart colors and styles
- Figure sizes
- Date formatting
- Chart titles and labels
- Grid and legend settings

### Example: Change Chart Style

```python
# In src/visualizations.py, modify plot_currency_trends()
plt.style.use('seaborn-v0_8-darkgrid')  # Use dark theme
# or
sns.set_style("whitegrid")  # Use seaborn style
```

## Output Location

Charts are saved to `data/exports/` by default. The filename format is:
- `chart_{type}_{date}.png`

For example:
- `chart_dashboard_20251222.png`
- `chart_currencies_20251222.png`

## Tips

1. **Collect data regularly**: More data points = better trends
2. **Use dashboard for overview**: Get all information at once
3. **Use specific charts for analysis**: Focus on what matters
4. **Compare assets**: Use comparison charts to see relative performance
5. **Automate**: Add chart generation to your daily update script

## Troubleshooting

**Problem**: "No data files found"
- **Solution**: Run `python scripts/daily_update.py` first to collect data

**Problem**: "matplotlib not installed"
- **Solution**: `pip install matplotlib seaborn pandas`

**Problem**: Chart looks empty
- **Solution**: Make sure you have multiple days of data (at least 2)

**Problem**: Can't see chart when using --show
- **Solution**: Use `--output` instead to save the file, or ensure you have a GUI environment

## Advanced: Creating Custom Visualizations

You can create your own visualization functions:

```python
from src.visualizations import load_historical_data
import matplotlib.pyplot as plt

# Load data
df = load_historical_data()

# Create custom chart
plt.figure(figsize=(10, 6))
# Your custom plotting code here
plt.savefig("custom_chart.png")
```

See `src/visualizations.py` for examples of how to work with the data.

