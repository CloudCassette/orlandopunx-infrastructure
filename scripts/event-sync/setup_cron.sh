#!/bin/bash

echo "🤖 Setting up automated Orlando Punk Events sync"
echo "==============================================="

# Create logs directory
mkdir -p /home/cloudcassette/logs

# Create the correct crontab entry
echo "Corrected crontab entry:"
echo "# Orlando Punk Events - Auto sync every 2 hours"
echo "0 */2 * * * cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync && /bin/bash -c 'source venv/bin/activate && GANCIO_PASSWORD=\"your-password-here\" python3 automated_sync_with_credentials.py' >> /home/cloudcassette/logs/orlandopunx-sync.log 2>&1"

echo ""
echo "📋 To add to your crontab:"
echo "1. Run: crontab -e"
echo "2. Add the line above (replace 'your-password-here' with actual password)"
echo "3. Save and exit"

echo ""
echo "🔒 For better security, you can also use environment variables:"
echo "# Add to your ~/.bashrc or ~/.profile:"
echo "export GANCIO_PASSWORD='your-password-here'"
echo ""
echo "# Then use this crontab entry instead:"
echo "0 */2 * * * cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync && /bin/bash -l -c 'source venv/bin/activate && python3 automated_sync_with_credentials.py' >> /home/cloudcassette/logs/orlandopunx-sync.log 2>&1"

echo ""
echo "✅ Setup script ready!"
