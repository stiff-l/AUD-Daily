# GitHub Actions Setup Guide

This repository uses GitHub Actions to automatically collect commodity and forex data daily at 5pm Cairns time (7am UTC).

## What It Does

The workflow (`/.github/workflows/daily_update.yml`) automatically:

1. **Collects Commodity Data** - Scrapes prices for Gold, Silver, Copper, Aluminium, Zinc, Nickel
2. **Collects Forex Data** - Fetches AUD exchange rates for USD, EUR, CNY, SGD, JPY
3. **Generates HTML** - Creates HTML visualizations for both commodities and forex
4. **Generates JPEG** - Converts HTML to JPEG images
5. **Commits Results** - Automatically commits HTML, JPEG, and CSV files to the repository

## Schedule

- **Runs daily at**: 5:00 PM AEST (Cairns time) = 7:00 AM UTC
- **Cron expression**: `0 7 * * *` (every day at 7am UTC)

## Manual Trigger

You can also trigger the workflow manually:
1. Go to the "Actions" tab in your GitHub repository
2. Select "Daily Data Collection" workflow
3. Click "Run workflow"

## Requirements

The workflow requires:
- Python 3.12
- All dependencies from `requirements.txt`
- Playwright (for HTML to JPEG conversion)
- System dependencies for headless browser

## What Gets Committed

The workflow commits:
- ✅ HTML files: `data/forex_data/HTML/` and `data/commodities_data/HTML/`
- ✅ JPEG files: `data/forex_data/JPEG/` and `data/commodities_data/JPEG/`
- ✅ CSV files: `currency_daily.csv` and `commodity_daily.csv`

The following are **NOT** committed (in `.gitignore`):
- ❌ Raw JSON files
- ❌ Processed JSON files
- ❌ Log files

## Setup

1. **Push the workflow file** to your repository:
   ```bash
   git add .github/workflows/daily_update.yml
   git commit -m "Add GitHub Actions workflow for daily data collection"
   git push
   ```

2. **Enable Actions** (if not already enabled):
   - Go to repository Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected
   - Save changes

3. **Set up permissions** (if needed):
   - Go to repository Settings → Actions → General → Workflow permissions
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"
   - Save changes

## Troubleshooting

### Workflow doesn't run
- Check that Actions are enabled in repository settings
- Verify the cron schedule is correct (7am UTC = 5pm AEST)
- Check the Actions tab for error messages

### Commits fail
- Ensure workflow has write permissions
- Check that GITHUB_TOKEN has proper permissions
- Verify .gitignore isn't blocking files that should be committed

### Scripts fail
- Check the Actions logs for specific error messages
- Verify all dependencies are in `requirements.txt`
- Ensure Playwright is properly installed

## Viewing Results

After the workflow runs:
1. Check the "Actions" tab to see run status
2. View committed files in the repository
3. HTML and JPEG files will be in their respective directories

## Notes

- The workflow runs even if your computer is off
- It uses GitHub's free tier (unlimited for public repos)
- Each run takes approximately 2-5 minutes
- Data is collected from TradingEconomics (commodities) and exchange rate APIs (forex)
