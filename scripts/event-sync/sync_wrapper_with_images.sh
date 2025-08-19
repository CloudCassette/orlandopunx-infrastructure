#!/bin/bash

# Orlando Punk Events Sync Wrapper
# This script loads the environment properly for cron jobs

# Load user environment (including GANCIO_PASSWORD)
source ~/.bashrc

# Change to the correct directory
cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync

# Activate virtual environment and run sync
source venv/bin/activate
python3 enhanced_sync_with_images.py
