# Setting Up Automatic Scheduling for Mineral Commodities

This guide explains how to set up automatic daily collection of mineral commodity data at 5pm Cairns time.

## macOS - Using launchd (Recommended)

### Step 1: Install the Launch Agent

1. Copy the plist file to your LaunchAgents directory:
   ```bash
   cp /Users/stephanel/AUD-Daily/com.auddaily.commodities.update.plist ~/Library/LaunchAgents/
   ```

2. Load the launch agent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.auddaily.commodities.update.plist
   ```

### Step 2: Verify Installation

Check if the agent is loaded:
```bash
launchctl list | grep auddaily
```

You should see `com.auddaily.commodities.update` in the list.

### Step 3: Test Manually

Before relying on automation, test the script manually:
```bash
cd /Users/stephanel/AUD-Daily
python3 scripts/Mineral_Commodities_Data_Collection/daily_update.py
```

### Step 4: Check Logs

Monitor the logs to verify it's running:
```bash
tail -f /Users/stephanel/AUD-Daily/logs/commodities_launchd.log
```

Check for errors:
```bash
tail -f /Users/stephanel/AUD-Daily/logs/commodities_launchd.error.log
```

### Unloading the Agent (if needed)

To stop automatic scheduling:
```bash
launchctl unload ~/Library/LaunchAgents/com.auddaily.commodities.update.plist
```

## Alternative: Using Cron

If you prefer cron instead of launchd:

1. Open your crontab:
   ```bash
   crontab -e
   ```

2. Add this line (adjust Python path if needed):
   ```cron
   0 7 * * * cd /Users/stephanel/AUD-Daily && /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 scripts/Mineral_Commodities_Data_Collection/daily_update.py >> logs/commodities_cron.log 2>&1
   ```

   Note: `0 7 * * *` means 7am UTC = 5pm AEST (Cairns time)

3. Verify:
   ```bash
   crontab -l
   ```

## Schedule Details

- **Time**: 5:00 PM AEST (Australian Eastern Standard Time)
- **Timezone**: Australia/Brisbane (UTC+10, no daylight saving)
- **Frequency**: Daily
- **Script**: `scripts/Mineral_Commodities_Data_Collection/daily_update.py`

## Troubleshooting

### Script doesn't run

1. **Check Python path**: Make sure the Python path in the plist file is correct:
   ```bash
   which python3
   ```
   Update the plist file if needed.

2. **Check file permissions**: Ensure the script is executable:
   ```bash
   chmod +x scripts/Mineral_Commodities_Data_Collection/daily_update.py
   ```

3. **Check logs**: Look for error messages in:
   - `logs/commodities_launchd.log`
   - `logs/commodities_launchd.error.log`

4. **Test manually**: Run the script manually to see if there are any errors:
   ```bash
   python3 scripts/Mineral_Commodities_Data_Collection/daily_update.py
   ```

### Time zone issues

- The launchd plist uses `Australia/Brisbane` timezone
- Cairns uses AEST (UTC+10) year-round (no daylight saving)
- Make sure your system timezone is set correctly

### Network issues

- The script requires internet access to fetch data from Metals.Dev API
- Make sure your computer is connected to the internet at 5pm AEST
- Ensure METALS_DEV_API_KEY is configured in config/settings.py

## Notes

- The script will collect data even if run outside of 5pm (it just prints a note)
- Data is saved to:
  - Raw: `data/commodities_data/raw/`
  - Processed: `data/commodities_data/processed/`
  - CSV: `data/commodities_data/processed/commodity_daily.csv`
  - HTML: `data/commodities_data/HTML/`
