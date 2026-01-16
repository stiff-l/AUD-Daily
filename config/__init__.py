"""
Configuration package for AUD Daily Tracker.

This package contains settings and configuration files.
settings.py is optional and can be created from settings.example.py.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Get the directory where this __init__.py file is located
_config_dir = Path(__file__).parent

# Try to import settings, with fallback to settings.example
try:
    from . import settings
except ImportError:
    try:
        # If settings.py doesn't exist, try to load settings.example.py
        # Note: settings.example.py has a dot in the filename, so we need to use importlib
        example_path = _config_dir / "settings.example.py"
        if example_path.exists():
            spec = importlib.util.spec_from_file_location("settings_example", example_path)
            if spec and spec.loader:
                settings_example = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(settings_example)
                settings = settings_example
                # Warn that example settings are being used
                import warnings
                warnings.warn(
                    "config/settings.py not found. Using example settings.",
                    UserWarning
                )
            else:
                raise ImportError("Could not load settings.example.py")
        else:
            raise ImportError("settings.example.py not found")
    except (ImportError, Exception) as e:
        # If neither exists, create a minimal settings object
        class MinimalSettings:
            """Minimal settings object when no config file is available."""
            pass
        
        settings = MinimalSettings()
        import warnings
        warnings.warn(
            f"No config settings found. Using minimal settings object. ({e})",
            UserWarning
        )

# Make settings available at package level
__all__ = ['settings']
