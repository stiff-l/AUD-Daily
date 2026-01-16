"""
Import Utilities Module

Helper functions for consistent imports across the codebase.
"""

import os
import sys
import importlib.util
from typing import Any, Optional


def safe_import_module(module_name: str, package_name: Optional[str] = None, fallback_path: Optional[str] = None) -> Optional[Any]:
    """
    Safely import a module with multiple fallback strategies.
    
    Args:
        module_name: Name of the module to import (e.g., "tradingeconomics_scraper")
        package_name: Package name if importing from a package (e.g., "src")
        fallback_path: Optional file path to try if other methods fail
        
    Returns:
        The imported module, or None if all import attempts fail
    """
    # Try relative import first (if package_name is provided)
    if package_name:
        try:
            return __import__(f"{package_name}.{module_name}", fromlist=[module_name])
        except ImportError:
            pass
    
    # Try absolute import
    try:
        return __import__(module_name)
    except ImportError:
        pass
    
    # Try with package prefix
    if package_name:
        try:
            return __import__(f"{package_name}.{module_name}")
        except ImportError:
            pass
    
    # Try loading from file path if provided
    if fallback_path and os.path.exists(fallback_path):
        try:
            spec = importlib.util.spec_from_file_location(module_name, fallback_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        except Exception:
            pass
    
    return None


def get_module_attribute(module: Any, attribute_name: str, default: Any = None) -> Any:
    """
    Safely get an attribute from a module.
    
    Args:
        module: The module object
        attribute_name: Name of the attribute to get
        default: Default value if attribute doesn't exist
        
    Returns:
        The attribute value or default
    """
    if module is None:
        return default
    return getattr(module, attribute_name, default)
