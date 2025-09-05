#!/usr/bin/env python3

# Configuration file example for remove_duplicates.py
# Copy this file to config.py and update with your actual values

# Gancio server configuration
BASE_URL = "http://localhost:3000"  # Update with your Gancio URL
# Examples:
# BASE_URL = "https://yourdomain.com"
# BASE_URL = "http://gancio.example.org"

# Admin login credentials
EMAIL = "your-admin-email@example.com"     # Your Gancio admin email
PASSWORD = "your-secure-password"          # Your Gancio admin password

# Safety settings
MAX_REMOVALS_PER_PAGE = 5    # Maximum duplicates to remove per page (safety limit)
MAX_PAGES_TO_PROCESS = 10    # Maximum pages to process
DELAY_BETWEEN_REMOVALS = 3   # Seconds to wait between each removal

# Browser settings
HEADLESS_MODE = False        # Set to True to run browser in background
BROWSER_TIMEOUT = 20         # Seconds to wait for page elements
