#!/bin/bash
# Local debug script to test the same environment as GitHub Actions

echo "🔧 LOCAL DEBUG SIMULATION - GitHub Actions Environment"
echo "======================================================"
echo ""

# Simulate the GitHub Actions working directory
cd "$(pwd)"
echo "📍 Working Directory: $(pwd)"
echo "🐛 User: $(whoami)"
echo "🐍 Python: $(python3 --version)"
echo ""

# Check Git status
echo "📊 Git Status:"
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git rev-parse --short HEAD)"
echo "Status: $(git status --porcelain | wc -l) uncommitted changes"
echo ""

# Environment variables check
echo "🔐 Environment Variables:"
echo "GANCIO_EMAIL: ${GANCIO_EMAIL:-'❌ NOT SET'}"
echo "GANCIO_PASSWORD: ${GANCIO_PASSWORD:+✅ SET}" 
echo "DISCORD_WEBHOOK_URL: ${DISCORD_WEBHOOK_URL:+✅ SET}"
echo ""

# Directory structure
echo "📁 Event Sync Directory:"
ls -la scripts/event-sync/ | head -10
echo ""

# Python environment
echo "🐍 Python Environment:"
cd scripts/event-sync
if [ -d "venv" ]; then
  echo "✅ Virtual environment exists"
  echo "venv contents:"
  ls -la venv/bin/ | grep -E "(python|pip|activate)" || echo "❌ Missing executables"
else
  echo "❌ Virtual environment missing"
fi
echo ""

# Network and services
echo "🌐 Network & Services:"
systemctl is-active gancio 2>/dev/null && echo "✅ Gancio service active" || echo "❌ Gancio service not active"

if ss -tuln | grep :13120 >/dev/null; then
  echo "✅ Port 13120 listening"
else
  echo "❌ Port 13120 not available"
fi

if curl -s --connect-timeout 5 http://localhost:13120 >/dev/null 2>&1; then
  echo "✅ Gancio web accessible"
  api_test=$(curl -s http://localhost:13120/api/events 2>/dev/null)
  if [ ! -z "$api_test" ] && [ "$api_test" != "null" ]; then
    echo "✅ Gancio API responding"
  else
    echo "❌ Gancio API not responding"
  fi
else
  echo "❌ Cannot connect to Gancio"
fi
echo ""

# Test script execution
echo "🚀 Script Test:"
if [ -d "venv" ]; then
  echo "Activating virtual environment..."
  source venv/bin/activate
  
  # Quick import test
  python3 -c "
import sys
import requests
print('✅ Basic imports successful')

try:
    from enhanced_multi_venue_sync import scrape_willspub_events
    print('✅ Event sync import successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    
# Test connection
try:
    resp = requests.get('http://localhost:13120/api/events', timeout=5)
    print(f'✅ API connection: {resp.status_code}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
" 2>&1
else
  echo "❌ Cannot test - no virtual environment"
fi

echo ""
echo "🎯 Debug Summary:"
echo "================="
echo "This simulates the GitHub Actions environment locally."
echo "Compare results with the failed GitHub Actions run to identify differences."
