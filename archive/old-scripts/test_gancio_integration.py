import json
import requests
import os
from datetime import datetime

print("🌐 Testing Gancio integration...")

# Load the scraped events
try:
    with open('willspub_events.json', 'r') as f:
        events = json.load(f)
    print(f"📋 Found {len(events)} events to process")
except:
    print("❌ No events file found")
    exit(1)

# Check if we have credentials (won't actually connect without them)
gancio_email = os.environ.get('GANCIO_EMAIL', 'test@example.com')
gancio_password = os.environ.get('GANCIO_PASSWORD', 'password')

print(f"📧 Gancio email configured: {gancio_email[:3]}...")
print(f"🔑 Gancio password configured: {'*' * len(gancio_password)}")

# Show what events would be added
print("\n🎯 Events that would be added to orlandopunx.com:")
for i, event in enumerate(events[:5]):  # Show first 5
    print(f"   {i+1}. {event.get('title', 'Unknown')} - {event.get('date', 'No date')}")

if len(events) > 5:
    print(f"   ... and {len(events) - 5} more events")

print(f"\n✅ Website integration test complete - {len(events)} events ready to sync")
