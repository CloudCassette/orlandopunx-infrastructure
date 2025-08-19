#!/bin/bash

# Orlando Punk Events Sync Wrapper - FIXED for cron environment issues
# This script properly loads the environment for cron jobs

echo "🤖 AUTOMATED ORLANDO PUNK EVENTS SYNC"
echo "=================================================="
echo "⏰ Started: $(date)"

# Explicitly set environment variables that cron needs
export HOME=/home/cloudcassette
export USER=cloudcassette
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export SHELL=/bin/bash

# Load user environment (including GANCIO_PASSWORD)
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Additional environment file if it exists
if [ -f ~/.profile ]; then
    source ~/.profile
fi

# Verify critical environment variables
if [ -z "$GANCIO_PASSWORD" ]; then
    echo "❌ GANCIO_PASSWORD not found in environment"
    echo "💡 Checking for environment file..."
    
    # Check if there's a local .env file
    if [ -f "/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/.env" ]; then
        echo "📁 Loading from .env file..."
        source /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/.env
    fi
    
    if [ -z "$GANCIO_PASSWORD" ]; then
        echo "❌ Still no GANCIO_PASSWORD. Exiting."
        exit 1
    fi
fi

# Set additional required environment variables
export GANCIO_EMAIL="godlessamericarecords@gmail.com"
export GANCIO_URL="http://localhost:13120"

echo "✅ Environment loaded successfully"
echo "🔐 GANCIO_EMAIL: $GANCIO_EMAIL"
echo "🔐 GANCIO_PASSWORD: ${GANCIO_PASSWORD:0:10}..."

# Change to the correct directory
cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Run the sync
echo "🎸 Starting Orlando events sync..."
python3 automated_sync_working.py

echo "✅ Sync completed: $(date)"
