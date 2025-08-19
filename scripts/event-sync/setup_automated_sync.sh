#!/bin/bash

echo "🤖 Setting up automated Gancio sync"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
# Gancio credentials for automation
GANCIO_EMAIL=godlessamericarecords@gmail.com
GANCIO_URL=http://localhost:13120
# GANCIO_PASSWORD=your-password-here
ENVEOF
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "📋 To complete setup:"
echo "1. Edit .env and add your GANCIO_PASSWORD"
echo "2. Or set environment variable: export GANCIO_PASSWORD='your-password'"
echo ""
echo "🚀 Then run: python3 automated_sync_with_credentials.py"
echo ""
echo "📅 For automated runs, add to crontab:"
echo "# Run every 2 hours"
echo "0 */2 * * * cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync && source venv/bin/activate && python3 automated_sync_with_credentials.py >> /home/cloudcassette/logs/orlandopunx-sync.log 2>&1"
