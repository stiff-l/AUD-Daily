# Setup Guide for Beginners

Welcome! This guide will help you set up your AUD Daily Tracker project step by step.

## What This Project Does

This project tracks the Australian Dollar (AUD) against:
- **Currencies**: USD, EUR, CNY
- **Commodities**: Gold, Silver, Copper  
- **Cryptocurrencies**: BTC, ETH, SOL, ZCASH

## Step-by-Step Setup

### Step 1: Install Python

1. Check if Python is installed:
   ```bash
   python3 --version
   ```
   You should see something like `Python 3.8.0` or higher.

2. If Python is not installed:
   - **Mac**: Install via Homebrew: `brew install python3`
   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - **Linux**: `sudo apt-get install python3` (Ubuntu/Debian)

### Step 2: Create Project Folders

The project structure is already set up, but here's what each folder does:

- **`src/`** - Your Python code files
- **`data/`** - Where collected data is stored
  - `raw/` - Raw data files with timestamps
  - `processed/` - Daily data files
  - `exports/` - Reports and exports
- **`config/`** - Configuration files (API keys, settings)
- **`scripts/`** - Scripts to run tasks
- **`docs/`** - Documentation
- **`notebooks/`** - Jupyter notebooks for analysis (optional)

### Step 3: Set Up Virtual Environment (Recommended)

A virtual environment keeps your project's dependencies separate from other projects.

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate it:
   - **Mac/Linux**: `source venv/bin/activate`
   - **Windows**: `venv\Scripts\activate`
   
   You should see `(venv)` at the start of your command prompt.

3. Deactivate when done:
   ```bash
   deactivate
   ```

### Step 4: Install Dependencies

1. Make sure your virtual environment is activated (you should see `(venv)`)

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

This installs:
- `pandas` - For data manipulation
- `requests` - For making API calls
- `python-dotenv` - For managing environment variables

### Step 5: Configure Settings

1. Copy the example settings file (if you haven't already):
   ```bash
   cp config/settings.example.py config/settings.py
   ```

2. Edit `config/settings.py` and add your API keys:

   **Current Status:**
   - ✅ **Currency API** - Already working! No API key needed (uses exchangerate-api.com)
   - ✅ **Crypto API** - Already working! No API key needed (uses CoinGecko)
   - ⚠️ **Commodity API** - Needs API key for full functionality

   **To Enable Commodity Prices (Gold, Silver, Copper):**
   
   1. Visit [metals-api.com](https://metals-api.com) and sign up for a free account
   2. Get your free API key from the dashboard
   3. Open `config/settings.py` in a text editor
   4. Find the line: `METALS_API_KEY = "your_metals_api_key_here"`
   5. Replace it with: `METALS_API_KEY = "your_actual_api_key_here"`
   
   **Example:**
   ```python
   METALS_API_KEY = "abc123xyz456"  # Your actual API key
   ```
   
   **Note:** The project will still work without the commodity API key, but commodity prices will show as `null`. Currency and crypto data will work perfectly without any API keys!

### Step 6: Test the Setup

1. Run the data collector to test:
   ```bash
   python src/data_collector.py
   ```

   This should fetch some data and print it to the console.

2. Run the daily update script:
   ```bash
   python scripts/daily_update.py
   ```

   This will:
   - Collect all data
   - Save it to `data/raw/` and `data/processed/`

3. Check that files were created:
   ```bash
   ls data/raw/
   ls data/processed/
   ```

### Step 7: Set Up Daily Automation (Optional)

To automatically collect data every day:

**On Mac/Linux:**
1. Open crontab: `crontab -e`
2. Add this line (runs daily at 9 AM):
   ```
   0 9 * * * cd /path/to/AUD-Daily && /path/to/venv/bin/python scripts/daily_update.py
   ```

**On Windows:**
1. Open Task Scheduler
2. Create a new task
3. Set it to run daily
4. Action: Run `python scripts/daily_update.py` in your project directory

## Understanding the Code

### `src/data_collector.py`
- Fetches data from APIs
- Functions: `fetch_currency_rates()`, `fetch_commodity_prices()`, `fetch_crypto_prices()`

### `src/data_storage.py`
- Saves and loads data files
- Functions: `save_raw_data()`, `save_daily_data()`, `load_data()`

### `scripts/daily_update.py`
- Main script that runs the daily collection
- Calls the collector and saves the data

## Next Steps

1. **Customize data sources**: Edit `src/data_collector.py` to use different APIs
2. **Add analysis**: Create Jupyter notebooks in `notebooks/` to analyze trends
3. **Create visualizations**: Generate charts and graphs from your data (see below)
4. **Set up alerts**: Add code to notify you of significant changes

### Creating Visualizations

Visualization libraries are already installed! You can create charts from your data:

**Generate a comprehensive dashboard:**
```bash
python scripts/generate_charts.py --type dashboard
```

**Generate specific chart types:**
```bash
# Currency trends
python scripts/generate_charts.py --type currencies

# Cryptocurrency trends
python scripts/generate_charts.py --type crypto

# Commodity trends
python scripts/generate_charts.py --type commodities

# Compare specific assets
python scripts/generate_charts.py --type comparison --assets USD EUR BTC ETH
```

**Limit to recent days:**
```bash
python scripts/generate_charts.py --type dashboard --days 30
```

**Save to specific location:**
```bash
python scripts/generate_charts.py --type dashboard --output my_chart.png
```

Charts are saved to `data/exports/` by default. See `docs/VISUALIZATION_GUIDE.md` for more details.

## Getting Help

- **Python basics**: [Python.org Tutorial](https://docs.python.org/3/tutorial/)
- **Working with APIs**: [Real Python - Working with APIs](https://realpython.com/python-api/)
- **Pandas tutorial**: [Pandas Getting Started](https://pandas.pydata.org/docs/getting_started/intro_tutorials/)

## Common Issues

**Problem**: `ModuleNotFoundError`
- **Solution**: Make sure you activated your virtual environment and installed requirements

**Problem**: API errors
- **Solution**: Check your internet connection and API key (if required)

**Problem**: Permission errors when saving files
- **Solution**: Make sure the `data/` directory exists and you have write permissions

## Tips for Beginners

1. **Start small**: Test each function individually before running the full script
2. **Read error messages**: They usually tell you what's wrong
3. **Use print statements**: Add `print()` to see what's happening
4. **Check the data files**: Open the JSON files to see what data you're collecting
5. **Experiment**: Try modifying the code to see what happens

Good luck with your project! 🚀

