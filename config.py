#!/usr/bin/env python3

# Configuration file for remove_duplicates.py
# Updated to process all events efficiently

# Gancio server configuration
BASE_URL = "https://orlandopunx.com"  # Update with your Gancio URL
# Examples:
# BASE_URL = "https://events.orlandopunx.com"
# BASE_URL = "http://gancio.example.org"

# Admin login credentials
EMAIL = "godlessamericarecords@gmail.com"     # Your Gancio admin email
PASSWORD = "Marmalade-Stapling-Watch7"          # Your Gancio admin password

# Processing settings - configured to handle all 849 events
MAX_REMOVALS_PER_PAGE = 50   # Process up to 50 duplicates per page (more efficient)
MAX_PAGES_TO_PROCESS = 100   # Process up to 100 pages (should cover all 849 events)
DELAY_BETWEEN_REMOVALS = 1   # Reduced delay for faster processing (1 second)

# Browser settings
HEADLESS_MODE = True        # Set to True to run browser in background
BROWSER_TIMEOUT = 60         # Increased timeout for stability
