# Setup Guide for Beginners

Welcome! This guide will help you set up your AUD Daily Tracker project step by step.

## What This Project Does

This project tracks the Australian Dollar (AUD) against major currencies:
- **USD** (US Dollar)
- **EUR** (Euro)
- **CNY** (Chinese Yuan)
- **SGD** (Singapore Dollar)

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
  - `forex_data/` - Forex data storage
    - `raw/` - Raw data files with timestamps (JSON)
    - `processed/` - Daily data files (JSON) and daily currency CSV
    - `historical/` - Historical RBA database and CSV (static, manually updated)
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
- `pandas` - For data manipulation and CSV table management
- `requests` - For making API calls
- `pytz` - For timezone handling (Cairns time)
- `python-dateutil` - For date/time parsing

### Step 5: Configure Settings

1. Copy the example settings file (if you haven't already):
   ```bash
   cp config/settings.example.py config/settings.py
   ```

2. Edit `config/settings.py` (optional):
   
   **Current Status:**
   - ✅ **Currency API** - Already working! No API key needed (uses exchangerate-api.com)
   
   The system works out of the box with free APIs. No configuration required!

### Step 6: Test the Setup

1. Run the data collector to test:
   ```bash
   python src/currency_collector.py
   ```

   This should fetch some data and print it to the console.

2. Run the daily update script:
   ```bash
   python scripts/daily_update.py
   ```

   This will:
   - Collect currency data (USD, EUR, CNY, SGD)
   - Save raw data to `data/forex_data/raw/` (JSON with timestamp)
   - Save processed data to `data/forex_data/processed/` (JSON by date)
   - Save to daily currency table `data/forex_data/processed/currency_daily.csv`

3. Check that files were created:
   ```bash
   ls data/forex_data/raw/
   ls data/forex_data/processed/
   ```

### Step 7: Set Up Daily Automation (Optional)

To automatically collect data every day at 5pm Cairns time:

**On Mac/Linux:**
1. Open crontab: `crontab -e`
2. Add this line (runs daily at 5pm AEST):
   ```
   0 17 * * * cd /path/to/AUD-Daily && /path/to/venv/bin/python scripts/daily_update.py
   ```

**On Windows:**
1. Open Task Scheduler
2. Create a new task
3. Set it to run daily at 5:00 PM
4. Action: Run `python scripts/daily_update.py` in your project directory

See `docs/SCHEDULING_GUIDE.md` for more detailed scheduling instructions.

## Understanding the Code

### `src/currency_collector.py`
- Fetches currency data from APIs
- Function: `fetch_currency_rates()` - Gets USD, EUR, CNY, SGD rates

### `src/currency_storage.py`
- Saves and loads data files
- Functions: `save_raw_data()`, `save_daily_data()`, `save_to_currency_table()`

### `src/currency_history.py`
- Manages CSV table for historical currency data
- Each day is a new row with timestamps

### `scripts/daily_update.py`
- Main script that runs the daily collection
- Collects currency data and saves to JSON + CSV table
- Can be run manually or scheduled (designed for 5pm Cairns time)

## Next Steps

1. **View your data**: Use `python scripts/view_data.py` to see collected data
2. **Analyze trends**: Open `data/forex_data/processed/currency_daily.csv` in Excel or a data analysis tool
3. **Query historical data**: Use `python scripts/query_rba_data.py` to query the RBA historical database
3. **Collect historical data**: Run `python scripts/collect_historical_data.py` to get quarterly data since 1966
4. **Customize**: Edit `src/currency_collector.py` to add more currencies if needed

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
