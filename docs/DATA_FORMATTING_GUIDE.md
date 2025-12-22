# Data Formatting Guide

This guide explains how to view and format your AUD Daily Tracker data.

## Standardized Data Format

All JSON files in `data/processed/` now use a standardized format:

```json
{
  "date": "2025-12-22",
  "timestamp": "2025-12-22T12:30:32.891664",
  "currencies": {
    "USD": {
      "rate": 0.661,
      "base": "AUD",
      "date": "2025-12-22"
    }
  },
  "commodities": {
    "GOLD": {
      "price_usd": 2500.00,
      "price_aud": 3782.00,
      "currency": "USD",
      "unit": "oz",
      "source": "metals-api.com"
    }
  },
  "cryptocurrencies": {
    "BTC": {
      "price_aud": 133955,
      "currency": "AUD"
    }
  }
}
```

## Viewing Your Data

Use the `view_data.py` script to display your data in different formats:

### List Available Dates
```bash
python scripts/view_data.py --list
```

### View Latest Data (Table Format)
```bash
python scripts/view_data.py
# or explicitly:
python scripts/view_data.py --format table
```

### View Specific Date
```bash
python scripts/view_data.py --date 2025-12-22
```

### Available Formats

#### 1. Table Format (Default)
Clean, organized table view:
```bash
python scripts/view_data.py --format table
```

#### 2. Summary Format
Brief summary with emojis:
```bash
python scripts/view_data.py --format summary
```

#### 3. JSON Format
Raw JSON output:
```bash
python scripts/view_data.py --format json
```

#### 4. CSV Format
Comma-separated values for spreadsheet import:
```bash
python scripts/view_data.py --format csv > data.csv
```

#### 5. Minimal Format
One-line summary:
```bash
python scripts/view_data.py --format minimal
```

#### 6. Detailed Format
Comprehensive report:
```bash
python scripts/view_data.py --format detailed
```

## Standardizing Existing Files

If you have old data files, standardize them:

```bash
python scripts/standardize_existing_data.py
```

This will:
- Create backups of your original files (`.backup` extension)
- Convert all files to the standardized format
- Preserve all your data

## Customizing Output

You can customize the output by editing `src/data_formatter.py`:

- **`format_table()`** - Modify table layout and columns
- **`format_summary()`** - Change summary style
- **`format_custom()`** - Create your own templates

### Example: Adding a Custom Format

Edit `src/data_formatter.py` and add to `format_custom()`:

```python
elif template == "my_custom":
    output = [f"Custom View - {data.get('date')}"]
    # Your custom formatting here
    return "\n".join(output)
```

Then use it:
```bash
python scripts/view_data.py --format my_custom
```

## Programmatic Usage

You can also use the formatter in your own scripts:

```python
from src.data_storage import load_latest_data
from src.data_formatter import standardize_data, format_table

# Load and standardize data
data = load_latest_data()
standardized = standardize_data(data)

# Format as table
print(format_table(standardized))
```

## Exporting Data

### Export to CSV
```bash
python scripts/view_data.py --format csv > exports/aud_data.csv
```

### Export to JSON
```bash
python scripts/view_data.py --format json > exports/aud_data.json
```

### Export Multiple Dates
```bash
# Create a script to export all dates
for date in $(python scripts/view_data.py --list | grep -o '[0-9-]*' | head -n -1); do
    python scripts/view_data.py --date $date --format csv >> exports/all_data.csv
done
```

## Tips

1. **Use table format** for quick viewing
2. **Use CSV format** for importing into Excel/Google Sheets
3. **Use JSON format** for programmatic access
4. **Use summary format** for daily briefings

## Troubleshooting

**Problem**: "No data files found"
- **Solution**: Run `python scripts/daily_update.py` first to collect data

**Problem**: Old format files not displaying correctly
- **Solution**: Run `python scripts/standardize_existing_data.py` to convert them

**Problem**: Import errors
- **Solution**: Make sure you're running from the project root directory

