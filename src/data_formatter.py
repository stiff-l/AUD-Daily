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
    
    Args:
        data: Raw data dictionary from collector
        
    Returns:
        Standardized data dictionary
    """
    standardized = {
        "date": None,
        "timestamp": datetime.now().isoformat(),
        "currencies": {},
        "commodities": {},
        "cryptocurrencies": {}
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
    
    # Standardize currencies
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
    
    # Standardize commodities
    if "commodities" in data:
        commodities_data = data["commodities"]
        if isinstance(commodities_data, dict) and "commodities" in commodities_data:
            commodities_data = commodities_data["commodities"]
        
        for symbol, info in commodities_data.items():
            standardized["commodities"][symbol] = {
                "price_usd": info.get("price"),
                "price_aud": info.get("price_aud"),
                "currency": info.get("currency", "USD"),
                "unit": info.get("unit", "oz" if symbol in ["GOLD", "SILVER"] else "lb"),
                "source": info.get("source"),
                "note": info.get("note")
            }
    
    # Standardize cryptocurrencies
    if "cryptocurrencies" in data:
        cryptos_data = data["cryptocurrencies"]
        if isinstance(cryptos_data, dict) and "cryptocurrencies" in cryptos_data:
            cryptos_data = cryptos_data["cryptocurrencies"]
        
        for symbol, info in cryptos_data.items():
            standardized["cryptocurrencies"][symbol] = {
                "price_aud": info.get("price_aud"),
                "currency": info.get("currency", "AUD")
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
    
    # Commodities section
    if data.get("commodities"):
        output.append("COMMODITIES")
        output.append("-" * 70)
        output.append(f"{'Commodity':<12} {'Price (USD)':<15} {'Price (AUD)':<15} {'Unit':<8}")
        output.append("-" * 70)
        for symbol, info in sorted(data["commodities"].items()):
            price_usd = info.get("price_usd")
            price_aud = info.get("price_aud")
            unit = info.get("unit", "N/A")
            
            price_usd_str = f"${price_usd:,.2f}" if price_usd else "N/A"
            price_aud_str = f"${price_aud:,.2f}" if price_aud else "N/A"
            
            output.append(f"{symbol:<12} {price_usd_str:<15} {price_aud_str:<15} {unit:<8}")
            if info.get("note"):
                output.append(f"  └─ {info['note']}")
        output.append("")
    
    # Cryptocurrencies section
    if data.get("cryptocurrencies"):
        output.append("CRYPTOCURRENCIES")
        output.append("-" * 70)
        output.append(f"{'Crypto':<12} {'Price (AUD)':<20}")
        output.append("-" * 70)
        for symbol, info in sorted(data["cryptocurrencies"].items()):
            price_aud = info.get("price_aud")
            price_str = f"${price_aud:,.2f}" if price_aud else "N/A"
            output.append(f"{symbol:<12} {price_str:<20}")
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
    
    # Commodities summary
    if data.get("commodities"):
        output.append("\n🏭 Commodities:")
        for symbol, info in sorted(data["commodities"].items()):
            price_aud = info.get("price_aud")
            if price_aud:
                output.append(f"   {symbol}: ${price_aud:,.2f} AUD/{info.get('unit', '')}")
            else:
                output.append(f"   {symbol}: Not available")
    
    # Crypto summary
    if data.get("cryptocurrencies"):
        output.append("\n₿ Cryptocurrencies:")
        for symbol, info in sorted(data["cryptocurrencies"].items()):
            price_aud = info.get("price_aud")
            if price_aud:
                output.append(f"   {symbol}: ${price_aud:,.2f} AUD")
    
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
    lines.append("Type,Asset,Value,Currency,Unit,Date")
    
    # Currencies
    for symbol, info in sorted(data.get("currencies", {}).items()):
        rate = info.get("rate", "")
        date = info.get("date", data.get("date", ""))
        lines.append(f"Currency,{symbol},{rate},AUD,rate,{date}")
    
    # Commodities
    for symbol, info in sorted(data.get("commodities", {}).items()):
        price_aud = info.get("price_aud", "")
        unit = info.get("unit", "")
        date = data.get("date", "")
        lines.append(f"Commodity,{symbol},{price_aud},AUD,{unit},{date}")
    
    # Cryptocurrencies
    for symbol, info in sorted(data.get("cryptocurrencies", {}).items()):
        price_aud = info.get("price_aud", "")
        date = data.get("date", "")
        lines.append(f"Cryptocurrency,{symbol},{price_aud},AUD,coin,{date}")
    
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

