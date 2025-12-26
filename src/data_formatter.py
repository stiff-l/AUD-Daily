"""
Data Formatter Module

Standardizes data structure and provides customizable output formatting.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import json


def standardize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize data structure to ensure consistent format.
    Only handles currencies: USD, EUR, CNY, SGD, JPY
    
    Args:
        data: Raw data dictionary from collector
        
    Returns:
        Standardized data dictionary
    """
    standardized = {
        "date": None,
        "timestamp": datetime.now().isoformat(),
        "currencies": {}
    }
    
    # Extract date from collection_date or use current date
    if "collection_date" in data:
        try:
            date_obj = datetime.fromisoformat(data["collection_date"].replace("Z", "+00:00"))
            standardized["date"] = date_obj.strftime("%Y-%m-%d")
        except:
            standardized["date"] = datetime.now().strftime("%Y-%m-%d")
    else:
        standardized["date"] = datetime.now().strftime("%Y-%m-%d")
    
    # Standardize currencies (USD, EUR, CNY, SGD)
    if "currencies" in data:
        currencies_data = data["currencies"]
        if isinstance(currencies_data, dict) and "currencies" in currencies_data:
            currencies_data = currencies_data["currencies"]
        
        for symbol, info in currencies_data.items():
            standardized["currencies"][symbol] = {
                "rate": info.get("rate"),
                "base": info.get("base", "AUD"),
                "date": info.get("date", standardized["date"])
            }
    
    return standardized


def format_table(data: Dict[str, Any], show_all: bool = True) -> str:
    """
    Format data as a table.
    
    Args:
        data: Standardized data dictionary
        show_all: If True, show all sections; if False, only show available data
        
    Returns:
        Formatted table string
    """
    output = []
    output.append("=" * 70)
    output.append(f"AUD Daily Tracker - {data.get('date', 'Unknown Date')}")
    output.append("=" * 70)
    output.append("")
    
    # Currencies section
    if data.get("currencies"):
        output.append("CURRENCIES (AUD Base)")
        output.append("-" * 70)
        output.append(f"{'Currency':<12} {'Rate':<15} {'Date':<12}")
        output.append("-" * 70)
        for symbol, info in sorted(data["currencies"].items()):
            rate = info.get("rate")
            rate_str = f"{rate:.4f}" if rate is not None else "N/A"
            date_str = info.get("date", "N/A")
            output.append(f"{symbol:<12} {rate_str:<15} {date_str:<12}")
        output.append("")
    
    output.append("=" * 70)
    return "\n".join(output)


def format_summary(data: Dict[str, Any]) -> str:
    """
    Format data as a brief summary.
    
    Args:
        data: Standardized data dictionary
        
    Returns:
        Formatted summary string
    """
    output = []
    output.append(f"\n📊 AUD Daily Summary - {data.get('date', 'Unknown Date')}\n")
    
    # Currencies summary
    if data.get("currencies"):
        output.append("💱 Currencies:")
        for symbol, info in sorted(data["currencies"].items()):
            rate = info.get("rate")
            if rate:
                output.append(f"   {symbol}: {rate:.4f}")
    
    output.append("")
    return "\n".join(output)


def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format data as pretty JSON.
    
    Args:
        data: Standardized data dictionary
        indent: JSON indentation level
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_csv(data: Dict[str, Any]) -> str:
    """
    Format data as CSV.
    
    Args:
        data: Standardized data dictionary
        
    Returns:
        CSV formatted string
    """
    lines = []
    lines.append("Type,Asset,Value,Currency,Base,Date")
    
    # Currencies
    for symbol, info in sorted(data.get("currencies", {}).items()):
        rate = info.get("rate", "")
        date = info.get("date", data.get("date", ""))
        base = info.get("base", "AUD")
        lines.append(f"Currency,{symbol},{rate},{symbol},{base},{date}")
    
    return "\n".join(lines)


def format_custom(data: Dict[str, Any], template: str = "default") -> str:
    """
    Format data using a custom template.
    
    Args:
        data: Standardized data dictionary
        template: Template name ('default', 'minimal', 'detailed')
        
    Returns:
        Formatted string based on template
    """
    if template == "minimal":
        output = [f"AUD Daily - {data.get('date', 'Unknown')}"]
        if data.get("currencies"):
            rates = [f"{s}: {i.get('rate', 0):.4f}" 
                    for s, i in sorted(data["currencies"].items())]
            output.append("Currencies: " + ", ".join(rates))
        return "\n".join(output)
    
    elif template == "detailed":
        output = []
        output.append(f"Detailed Report - {data.get('date', 'Unknown Date')}")
        output.append(f"Timestamp: {data.get('timestamp', 'N/A')}")
        output.append("")
        output.append(format_table(data))
        return "\n".join(output)
    
    else:  # default
        return format_table(data)

