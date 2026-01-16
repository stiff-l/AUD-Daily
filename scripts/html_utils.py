"""
HTML Utilities Module

Shared utilities for HTML generation and JPEG conversion used by both
forex and commodity HTML generation scripts.
"""

import os
from typing import Optional

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import WebDriverException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def generate_arrow_html(current_value: float, previous_value: float, arrow_class: str = "arrow") -> str:
    """
    Generate arrow HTML based on value comparison.
    
    Args:
        current_value: Current day's value
        previous_value: Previous day's value
        arrow_class: CSS class prefix for the arrow (e.g., "currency-arrow" or "commodity-arrow")
        
    Returns:
        HTML string for the arrow icon, or empty string if no comparison possible
    """
    if current_value is None or previous_value is None:
        return ""
    
    try:
        current = float(current_value)
        previous = float(previous_value)
        
        if current > previous:
            # Value is up - green up arrow
            return f'<div class="{arrow_class} arrow-up"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7 14L12 9L17 14H7Z" fill="currentColor"/></svg></div>'
        elif current < previous:
            # Value is down - red down arrow
            return f'<div class="{arrow_class} arrow-down"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7 10L12 15L17 10H7Z" fill="currentColor"/></svg></div>'
        else:
            # No change - white dash
            return f'<div class="{arrow_class} arrow-neutral"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><line x1="7" y1="12" x2="17" y2="12" stroke="currentColor" stroke-width="3"/></svg></div>'
    except (ValueError, TypeError):
        return ""


def html_to_jpeg_playwright(html_path: str, jpeg_path: str, width: int = 1080, height: int = 1350) -> Optional[str]:
    """
    Convert HTML file to JPEG using Playwright with Chromium (primary method).
    Uses Chromium instead of Firefox due to Firefox Nightly compatibility issues on macOS.
    
    Args:
        html_path: Path to the HTML file
        jpeg_path: Path where the JPEG should be saved
        width: Width of the output image in pixels (default: 1080)
        height: Height of the output image in pixels (default: 1350)
        
    Returns:
        Path to the generated JPEG file, or None if conversion failed
    """
    if not PLAYWRIGHT_AVAILABLE:
        return None
    
    html_abs_path = os.path.abspath(html_path)
    html_file_url = f"file://{html_abs_path.replace(os.sep, '/')}"
    
    try:
        print("  Using Playwright with Chromium...")
        with sync_playwright() as p:
            # Launch Chromium browser (more stable on macOS than Firefox Nightly)
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as launch_error:
                print(f"    Chromium launch failed: {launch_error}")
                print("    Make sure Chromium is installed: python3 -m playwright install chromium")
                return None
            
            try:
                # Create context with viewport
                context = browser.new_context(
                    viewport={'width': width, 'height': height}
                )
                page = context.new_page()
                
                # Load HTML file with proper error handling
                try:
                    page.goto(html_file_url, wait_until='load', timeout=30000)
                except Exception as nav_error:
                    print(f"    Navigation error: {nav_error}")
                    context.close()
                    browser.close()
                    return None
                
                # Wait for page to fully render
                page.wait_for_timeout(1500)  # Give time for fonts/images to load
                
                # Take screenshot
                page.screenshot(path=jpeg_path, type="jpeg", quality=95, full_page=True)
                
                context.close()
                browser.close()
                
                print(f"✓ JPEG generated successfully with Playwright (Chromium): {jpeg_path}")
                return jpeg_path
                
            except Exception as screenshot_error:
                print(f"    Screenshot failed: {screenshot_error}")
                try:
                    context.close()
                    browser.close()
                except:
                    pass
                return None
                    
    except Exception as e:
        print(f"    Playwright (Chromium) error: {e}")
        return None


def html_to_jpeg_selenium(html_path: str, jpeg_path: str, width: int = 1080, height: int = 1350) -> Optional[str]:
    """
    Convert HTML file to JPEG using Selenium (fallback method).
    Uses Firefox as preferred browser.
    
    Args:
        html_path: Path to the HTML file
        jpeg_path: Path where the JPEG should be saved
        width: Width of the output image in pixels (default: 1080)
        height: Height of the output image in pixels (default: 1350)
        
    Returns:
        Path to the generated JPEG file, or None if conversion failed
    """
    if not SELENIUM_AVAILABLE:
        return None
    
    driver = None
    try:
        html_abs_path = os.path.abspath(html_path)
        html_file_url = f"file://{html_abs_path.replace(os.sep, '/')}"
        
        # Try Firefox first (user preference)
        try:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')
            firefox_options.set_preference("general.useragent.override", "Mozilla/5.0")
            
            driver = webdriver.Firefox(options=firefox_options)
            driver.set_window_size(width, height)
            print("  Using Firefox for Selenium fallback")
        except (WebDriverException, Exception) as e:
            print(f"  Firefox not available: {e}")
            return None
        
        if driver is None:
            return None
        
        # Load the HTML file
        driver.get(html_file_url)
        
        # Wait for page to load
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # Additional wait for any dynamic content
            import time
            time.sleep(1)
        except TimeoutException:
            print("  Warning: Page load timeout, proceeding anyway...")
        
        # Take screenshot
        driver.save_screenshot(jpeg_path)
        
        # Convert PNG to JPEG if needed (Selenium saves as PNG)
        if jpeg_path.lower().endswith('.jpg') or jpeg_path.lower().endswith('.jpeg'):
            try:
                from PIL import Image
                img = Image.open(jpeg_path)
                # Convert RGBA to RGB if needed
                if img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                img.save(jpeg_path, 'JPEG', quality=95)
            except ImportError:
                # PIL not available, keep PNG
                pass
            except Exception as e:
                print(f"  Warning: Could not convert to JPEG: {e}")
        
        print(f"✓ JPEG generated successfully with Selenium: {jpeg_path}")
        return jpeg_path
        
    except Exception as e:
        print(f"  Error with Selenium: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def html_to_jpeg(html_path: str, jpeg_path: str, width: int = 1080, height: int = 1350) -> Optional[str]:
    """
    Convert HTML file to JPEG image using multiple fallback methods.
    Tries Playwright first (primary), then Selenium as fallback.
    
    Args:
        html_path: Path to the HTML file
        jpeg_path: Path where the JPEG should be saved
        width: Width of the output image in pixels (default: 1080)
        height: Height of the output image in pixels (default: 1350)
        
    Returns:
        Path to the generated JPEG file, or None if conversion failed
    """
    # Try Playwright first (primary method)
    if PLAYWRIGHT_AVAILABLE:
        print("  Attempting conversion with Playwright...")
        result = html_to_jpeg_playwright(html_path, jpeg_path, width, height)
        if result:
            return result
    
    # Fallback to Selenium
    if SELENIUM_AVAILABLE:
        print("  Attempting conversion with Selenium (Firefox)...")
        result = html_to_jpeg_selenium(html_path, jpeg_path, width, height)
        if result:
            return result
    
    # If both failed
    if not PLAYWRIGHT_AVAILABLE and not SELENIUM_AVAILABLE:
        print("Warning: Neither Playwright nor Selenium available.")
        print("  Install Playwright: pip install playwright && python3 -m playwright install chromium")
        print("  Install Selenium: pip install selenium")
    else:
        print("Warning: Both Playwright and Selenium failed to convert HTML to JPEG")
        if PLAYWRIGHT_AVAILABLE:
            print("  Playwright troubleshooting:")
            print("    - Run: python3 -m playwright install chromium")
            print("    - Note: Using Chromium instead of Firefox due to Firefox Nightly crashes on macOS")
            print("    - Check browser binaries are installed correctly")
    
    return None
