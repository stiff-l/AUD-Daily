# Playwright Troubleshooting Guide

## Why Playwright Might Be Closing Unexpectedly

### Common Issues

1. **Browser Binaries Not Installed**
   - **Error**: `Executable doesn't exist at /Users/.../ms-playwright/chromium_headless_shell-.../chrome-headless-shell`
   - **Cause**: Playwright Python package is installed, but the browser binaries are missing
   - **Solution**: Run `python3 -m playwright install firefox`

2. **Installation Command Failing Silently**
   - If `python3 -m playwright install chromium` appears to run but doesn't work:
     - Check if you're in a virtual environment: `which python3`
     - Try: `python3 -m playwright install --help` to verify it's working
     - Check installation path: `python3 -c "from playwright.sync_api import sync_playwright; print(sync_playwright)"`

3. **Permission Issues**
   - Browser binaries might not have execute permissions
   - **Solution**: 
     ```bash
     chmod +x ~/Library/Caches/ms-playwright/*/chrome-headless-shell
     ```

4. **Context Manager Closing Too Early**
   - The `with sync_playwright()` context might close before screenshot completes
   - **Fixed in code**: Added proper error handling and explicit context/browser closing

5. **Browser Process Crashes**
   - Can happen due to resource limits or missing dependencies
   - **Solution**: The updated code tries multiple browser types (chromium, firefox, webkit) as fallbacks

## Installation Steps

### Step 1: Verify Playwright Python Package
```bash
pip list | grep playwright
# Should show: playwright >= 1.40.0
```

### Step 2: Install Browser Binaries
```bash
# Install Firefox (required for this project)
python3 -m playwright install firefox
```

### Step 3: Verify Installation
```bash
# Check if browsers are installed
python3 -m playwright install --dry-run chromium
```

### Step 4: Test Playwright
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print("Playwright is working!")
    browser.close()
```

## What the Updated Code Does

1. **Uses Firefox Only**: Uses Firefox for Playwright (as preferred)
2. **Better Error Handling**: Catches and reports specific errors clearly
3. **Proper Cleanup**: Explicitly closes context and browser even on errors
4. **Longer Wait Times**: Gives more time for fonts/images to load (1500ms)
5. **Fallback to Selenium**: If Playwright fails, falls back to Selenium with Firefox

## Debugging Tips

### Check Browser Installation Location
```bash
# macOS
ls -la ~/Library/Caches/ms-playwright/

# Should show directories like:
# firefox-1234/
```

### Run with Verbose Output
The updated code now prints which browser type it's trying, making it easier to see where it fails.

### Check System Requirements
- macOS: Should work out of the box
- Linux: May need additional dependencies: `playwright install-deps`
- Windows: Should work out of the box

## Firefox is the Primary Browser

This project uses Firefox exclusively for Playwright. Make sure Firefox is installed:
```bash
python3 -m playwright install firefox
```

## Still Having Issues?

1. **Check Python Version**: Playwright requires Python 3.8+
   ```bash
   python3 --version
   ```

2. **Reinstall Playwright**:
   ```bash
   pip uninstall playwright
   pip install playwright
   python3 -m playwright install chromium
   ```

3. **Check Virtual Environment**: Make sure you're installing in the correct environment
   ```bash
   which python3
   source venv/bin/activate  # if using venv
   python3 -m playwright install chromium
   ```

4. **Use Selenium Fallback**: The code will automatically use Selenium (Firefox) if Playwright fails
