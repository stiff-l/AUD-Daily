#!/usr/bin/env python3
"""
Unified Daily Update Script

Runs both forex and commodities data collection in a single script.
This script orchestrates both data collection processes:
- Forex data (USD, EUR, CNY, SGD, JPY)
- Commodities data (Gold, Silver, Copper, Aluminium, Nickel)

Can be run manually or scheduled (e.g., via GitHub Actions, cron, launchd).

Designed to run at 5pm Cairns time (AEST - UTC+10) for COB updates.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import update utilities
try:
    from scripts.update_utils import get_cairns_time, is_cob_time
except ImportError:
    try:
        from update_utils import get_cairns_time, is_cob_time
    except ImportError:
        # Fallback - define minimal versions if update_utils not available
        def get_cairns_time():
            from datetime import timezone, timedelta
            return datetime.now(timezone(timedelta(hours=10)))
        
        def is_cob_time():
            return False


def run_forex_update():
    """Run forex data collection and generation."""
    print("\n" + "=" * 70)
    print("FOREX DATA COLLECTION")
    print("=" * 70)
    
    try:
        # Import forex update function
        from scripts.Forex_Data_Collection.daily_update import main as forex_main
        
        # Run forex collection (may call sys.exit, so catch SystemExit)
        try:
            forex_main()
            return True, None
        except SystemExit as e:
            # Script called sys.exit() - check exit code
            if e.code == 0:
                return True, None
            else:
                return False, f"Forex update exited with code {e.code}"
        
    except Exception as e:
        error_msg = f"Forex update failed: {e}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg


def run_commodities_update():
    """Run commodities data collection and generation."""
    print("\n" + "=" * 70)
    print("COMMODITIES DATA COLLECTION")
    print("=" * 70)
    
    try:
        # Import commodities update function
        from scripts.Mineral_Commodities_Data_Collection.daily_update import main as commodities_main
        
        # Run commodities collection (may call sys.exit, so catch SystemExit)
        try:
            commodities_main()
            return True, None
        except SystemExit as e:
            # Script called sys.exit() - check exit code
            if e.code == 0:
                return True, None
            else:
                return False, f"Commodities update exited with code {e.code}"
        
    except Exception as e:
        error_msg = f"Commodities update failed: {e}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg


def main():
    """Main function to run both forex and commodities data collection."""
    print("=" * 70)
    print("AUD Daily Tracker - Unified Data Collection")
    print("Collecting: Forex (USD, EUR, CNY, SGD, JPY) + Commodities (Gold, Silver, Copper, Aluminium, Nickel)")
    print("=" * 70)
    
    cairns_time = get_cairns_time()
    print(f"Current Cairns time: {cairns_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Target time: 5:00 PM AEST (COB)")
    print()
    
    # Check if it's COB time (optional - can be run manually anytime)
    if not is_cob_time():
        print("Note: Not currently COB time, but proceeding with update...")
        print()
    
    # Track results
    results = {
        'forex': {'success': False, 'error': None},
        'commodities': {'success': False, 'error': None}
    }
    
    # Run forex update
    forex_success, forex_error = run_forex_update()
    results['forex']['success'] = forex_success
    results['forex']['error'] = forex_error
    
    # Run commodities update (even if forex failed)
    commodities_success, commodities_error = run_commodities_update()
    results['commodities']['success'] = commodities_success
    results['commodities']['error'] = commodities_error
    
    # Print summary
    print("\n" + "=" * 70)
    print("UNIFIED UPDATE SUMMARY")
    print("=" * 70)
    print(f"Forex:        {'✓ SUCCESS' if results['forex']['success'] else '✗ FAILED'}")
    if results['forex']['error']:
        print(f"  Error: {results['forex']['error']}")
    
    print(f"Commodities:  {'✓ SUCCESS' if results['commodities']['success'] else '✗ FAILED'}")
    if results['commodities']['error']:
        print(f"  Error: {results['commodities']['error']}")
    
    print("=" * 70)
    
    # Exit with appropriate code
    if results['forex']['success'] and results['commodities']['success']:
        print("✓ All data collection completed successfully!")
        return 0
    elif results['forex']['success'] or results['commodities']['success']:
        print("⚠ Partial success - one or more collections failed")
        return 1
    else:
        print("❌ All data collections failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
