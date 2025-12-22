# Notes

Project structure snapshot:

```
AUD-Daily/
├── .github/
│   └── workflows/
│       ├── daily-carousel.yml       # Runs at 5 PM daily
│       └── special-snapshot.yml     # Runs at 9 AM on special days
├── src/
│   ├── fetch_metals.py              # Fetch from Metals API
│   ├── fetch_currencies.py          # Fetch AUD/USD, etc.
│   ├── calculate_trends.py          # 7-day MA, high/low
│   ├── generate_carousel.py         # Create Instagram images
│   └── upload_drive.py              # Upload to Google Drive
├── data/
│   ├── processed/
│   │   └── metals_history.csv       # Growing daily history
│   ├── archives/
│   │   └── metals_snapshots.csv     # Special day snapshots
│   └── exports/
│       └── carousel_YYYYMMDD/       # Daily generated images
├── templates/
│   ├── slide_1_overview.png
│   ├── slide_2_gold.png
│   └── slide_3_silver.png
├── .env                              # API keys (not in Git)
├── .github-env                       # Template for GitHub secrets
└── requirements.txt
```

Daily Workflow (5 PM Cairns Time) 5:00 PM AEST (GitHub Actions triggers)

├── 1. Fetch metals data (API call)
├── 2. Append to history file (data/processed/metals_history.csv)
├── 3. Calculate trends (7-day MA, week high/low, month high/low)
├── 4. Generate Instagram carousel (overlay data on templates)
├── 5. Upload carousel to Google Drive
└── 6. Send notification (optional: email/Slack that it's ready)

Special Days Workflow (9 AM Cairns Time on 1st, 5th, 10th, 15th, 20th, 25th, 30th, last day)

9:00 AM AEST (GitHub Actions triggers)

├── 1. Fetch metals data (API call)
├── 2. Append to analysis archive (data/archives/metals_snapshots.csv)
└── 3. Store for future monthly reports

