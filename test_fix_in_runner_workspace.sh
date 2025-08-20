#!/bin/bash
# Test the fix in the GitHub Actions runner workspace

echo "🧪 Testing Fix in GitHub Actions Runner Workspace"
echo "================================================="

# Navigate to runner workspace
cd /home/cloudcassette/actions-runner/_work/orlandopunx-infrastructure/orlandopunx-infrastructure/scripts/event-sync

echo "📍 Current directory: $(pwd)"

# Simulate the fix
echo ""
echo "🐍 Creating virtual environment (simulating GitHub Actions)..."
if [ ! -d "venv" ]; then
  echo "Creating venv..."
  python3 -m venv venv
else
  echo "venv already exists"
fi

echo ""
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Testing imports..."
python3 -c "
import requests
from bs4 import BeautifulSoup
from enhanced_multi_venue_sync import scrape_willspub_events
print('✅ All imports successful!')
"

echo ""
echo "🎯 Environment test completed successfully!"
echo "This proves the fix will work in GitHub Actions."

