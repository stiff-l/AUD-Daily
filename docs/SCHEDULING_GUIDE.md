# Scheduling Guide

This guide explains how to schedule the AUD Daily Tracker to run automatically at 5pm Cairns time (COB).

## Time Zone Information

- **Cairns, Australia** uses **AEST (Australian Eastern Standard Time)**
- AEST is **UTC+10** year-round (no daylight saving time)
- **5pm AEST = 7am UTC**

## Scheduling Options

### Option 1: macOS/Linux - Using Cron

1. **Open your crontab**:
   ```bash
   crontab -e
   ```

2. **Add this line** (adjust paths as needed):
   ```cron
   0 7 * * * cd /Users/stephanel/AUD-Daily && /Users/stephanel/AUD-Daily/venv/bin/python scripts/scheduled_update.py >> logs/cron.log 2>&1
   ```

   Or if using system Python:
   ```cron
   0 7 * * * cd /Users/stephanel/AUD-Daily && python3 scripts/scheduled_update.py >> logs/cron.log 2>&1
   ```

3. **Cron format explanation**:
   ```
   0 7 * * *
   │ │ │ │ │
   │ │ │ │ └── Day of week (0-7, 0 and 7 = Sunday)
   │ │ │ └──── Month (1-12)
   │ │ └────── Day of month (1-31)
   │ └──────── Hour (0-23, UTC time)
   └────────── Minute (0-59)
   ```

4. **Verify your cron job**:
   ```bash
   crontab -l
   ```

5. **Test the cron job** (run manually first):
   ```bash
   python scripts/scheduled_update.py
   ```

### Option 2: macOS - Using launchd (LaunchAgent)

1. **Create a plist file** at `~/Library/LaunchAgents/com.auddaily.update.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.auddaily.update</string>
       <key>ProgramArguments</key>
       <array>
           <string>/Users/stephanel/AUD-Daily/venv/bin/python</string>
           <string>/Users/stephanel/AUD-Daily/scripts/scheduled_update.py</string>
       </array>
       <key>StandardOutPath</key>
       <string>/Users/stephanel/AUD-Daily/logs/launchd.log</string>
       <key>StandardErrorPath</key>
       <string>/Users/stephanel/AUD-Daily/logs/launchd.error.log</string>
       <key>StartCalendarInterval</key>
       <dict>
           <key>Hour</key>
           <integer>17</integer>
           <key>Minute</key>
           <integer>0</integer>
           <key>TimeZone</key>
           <string>Australia/Brisbane</string>
       </dict>
   </dict>
   </plist>
   ```

2. **Load the launch agent**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.auddaily.update.plist
   ```

3. **Check if it's loaded**:
   ```bash
   launchctl list | grep auddaily
   ```

4. **Unload (if needed)**:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.auddaily.update.plist
   ```

### Option 3: Windows - Using Task Scheduler

1. **Open Task Scheduler** (search for it in Start menu)

2. **Create Basic Task**:
   - Name: "AUD Daily Tracker Update"
   - Description: "Daily update at 5pm Cairns time"

3. **Set Trigger**:
   - Daily
   - Start time: 5:00 PM
   - Timezone: **(UTC+10:00) Brisbane** (important!)
   - Repeat: Every 1 day

4. **Set Action**:
   - Action: Start a program
   - Program/script: `C:\Python39\python.exe` (or your Python path)
   - Add arguments: `scripts\scheduled_update.py`
   - Start in: `C:\path\to\AUD-Daily`

5. **Set Conditions** (optional):
   - Uncheck "Start the task only if the computer is on AC power" (if you want it to run on battery)

6. **Test the task**:
   - Right-click the task > Run

## Verifying the Schedule

### Check Logs

The script logs to `logs/cron.log` (for cron) or `logs/launchd.log` (for launchd). Check these files to verify runs:

```bash
tail -f logs/cron.log
```

### Manual Test

Always test manually before scheduling:

```bash
python scripts/scheduled_update.py
```

### Check Current Time

The script displays the current Cairns time when it runs. Verify it's running at the correct time.

## Troubleshooting

### Script doesn't run

1. **Check file permissions**:
   ```bash
   chmod +x scripts/scheduled_update.py
   ```

2. **Check Python path**: Ensure the Python path in your cron/scheduler is correct

3. **Check working directory**: The script needs to run from the project root

4. **Check logs**: Look for error messages in log files

### Time zone issues

- The script uses `pytz` to handle timezones correctly
- Cairns uses AEST (UTC+10) year-round
- Make sure your scheduler is set to the correct timezone

## Alternative: Run at Different Times

If you want to run at a different time, modify the cron/scheduler settings:

- **9am AEST**: `0 23 * * *` (11pm UTC previous day)
- **12pm AEST**: `0 2 * * *` (2am UTC)
- **5pm AEST**: `0 7 * * *` (7am UTC) - **Default COB time**

