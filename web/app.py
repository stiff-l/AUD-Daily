#!/usr/bin/env python3
"""
AUD Daily Tracker - Web Dashboard

Flask web application to display current rates and historical trends.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_storage import load_latest_data, load_data
from src.data_formatter import standardize_data
from src.visualizations import load_historical_data

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


def load_historical_json_data():
    """Load historical quarterly data from JSON files."""
    historical_dir = Path("data/historical")
    if not historical_dir.exists():
        return None
    
    # Find the most recent historical data file
    json_files = list(historical_dir.glob("aud_historical_quarterly_*.json"))
    if not json_files:
        return None
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/current')
def api_current():
    """API endpoint for current data."""
    data = load_latest_data()
    if data:
        return jsonify(data)
    return jsonify({"error": "No current data available"}), 404


@app.route('/api/historical')
def api_historical():
    """API endpoint for historical data from processed files."""
    try:
        df = load_historical_data(days=365)  # Last year of daily data
        # Convert DataFrame to JSON
        records = df.to_dict('records')
        return jsonify({
            "success": True,
            "data": records,
            "count": len(records)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/historical/quarterly')
def api_historical_quarterly():
    """API endpoint for quarterly historical data."""
    data = load_historical_json_data()
    if data:
        return jsonify(data)
    return jsonify({"error": "No historical quarterly data available"}), 404


@app.route('/api/summary')
def api_summary():
    """API endpoint for summary statistics."""
    current = load_latest_data()
    historical = load_historical_json_data()
    
    summary = {
        "current_date": datetime.now().isoformat(),
        "current_data_available": current is not None,
        "historical_data_available": historical is not None
    }
    
    if current:
        summary["latest_date"] = current.get("date")
        if "currencies" in current:
            summary["currencies"] = list(current["currencies"].keys())
        if "commodities" in current:
            summary["commodities"] = list(current["commodities"].keys())
        if "cryptocurrencies" in current:
            summary["cryptocurrencies"] = list(current["cryptocurrencies"].keys())
    
    if historical:
        summary["historical_start_year"] = historical.get("start_year")
        summary["historical_end_year"] = historical.get("end_year")
        summary["historical_frequency"] = historical.get("frequency")
        for currency, rates in historical.get("currencies", {}).items():
            if rates:
                summary[f"{currency}_data_points"] = len(rates)
    
    return jsonify(summary)


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    template_dir = Path(__file__).parent / 'templates'
    template_dir.mkdir(exist_ok=True)
    
    print("Starting AUD Daily Tracker Web Dashboard...")
    print("Open your browser to: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)

