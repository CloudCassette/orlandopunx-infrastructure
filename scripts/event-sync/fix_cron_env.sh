#!/bin/bash

echo "🔧 FIXING CRON ENVIRONMENT VARIABLE ISSUE"
echo "========================================"

echo "The cron job can't access GANCIO_PASSWORD from .bashrc"
echo "We need to set it directly in the cron command."
echo ""
echo "Current crontab entry:"
crontab -l | grep "Orlando Punk" -A 1

echo ""
echo "🔒 SOLUTION OPTIONS:"
echo ""
echo "Option 1: Set password directly in crontab (quick but less secure)"
echo "Replace the current cron entry with:"
echo "0 */2 * * * cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync && GANCIO_PASSWORD='your-password-here' /bin/bash -l -c 'source venv/bin/activate && python3 automated_sync_working.py' >> /home/cloudcassette/logs/orlandopunx-sync.log 2>&1"
echo ""
echo "Option 2: Create a wrapper script (more secure)"
echo "I can create a wrapper script that loads the environment properly."
echo ""
echo "Which option would you prefer?"
echo "1) Quick fix - set password in cron"
echo "2) Secure fix - create wrapper script"
