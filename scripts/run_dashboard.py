#!/usr/bin/env python3
"""
Run Web Dashboard

Simple script to start the Flask web dashboard.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("AUD Daily Tracker - Web Dashboard")
    print("=" * 60)
    print()
    print("Starting server...")
    print("Open your browser to: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='127.0.0.1', port=5000)

