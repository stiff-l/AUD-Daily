"""
Update Utilities Module

Shared utilities for daily update scripts used by both forex and commodity updates.
"""

from datetime import datetime
import pytz


def get_cairns_time():
    """
    Get current time in Cairns (AEST - UTC+10, no daylight saving).
    
    Returns:
        datetime object in AEST timezone
    """
    # Cairns is in Queensland, which uses AEST (UTC+10) year-round
    cairns_tz = pytz.timezone('Australia/Brisbane')  # Brisbane uses same timezone as Cairns
    return datetime.now(cairns_tz)


def is_cob_time():
    """
    Check if current time is close to COB (5pm Cairns time).
    
    Returns:
        True if within 1 hour of 5pm AEST, False otherwise
    """
    cairns_time = get_cairns_time()
    hour = cairns_time.hour
    
    # Check if it's around 5pm (17:00) - allow 1 hour window
    return 16 <= hour <= 18
