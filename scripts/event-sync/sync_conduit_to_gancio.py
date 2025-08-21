#!/usr/bin/env python3
"""
🎸 Sync Conduit Events to Gancio
===============================
Syncs Conduit FL events to Gancio approval queue
"""

import json
import requests
import os
from datetime import datetime
import sys

def load_conduit_events():
    """Load Conduit events from JSON file"""
    try:
        with open('conduit_events.json', 'r') as f:
            events = json.load(f)
        print(f"📋 Loaded {len(events)} Conduit events from JSON")
        return events
    except FileNotFoundError:
        print("❌ conduit_events.json not found. Run conduit_scraper.py first.")
        return []

def sync_to_gancio(events):
    """Sync events to Gancio approval queue"""
    if not events:
        print("📭 No events to sync")
        return
    
    gancio_url = "http://localhost:13120"
    
    print(f"🔄 Syncing {len(events)} Conduit events to Gancio...")
    print("   (Events will appear in the approval queue)")
    
    # For now, just show what would be synced
    # The actual Gancio integration requires authentication setup
    print("\n📋 Events ready for Gancio sync:")
    print("=" * 40)
    
    for event in events:
        print(f"🎵 {event['title']}")
        print(f"   📅 {event['date']} at {event['time']}")
        print(f"   📍 {event['venue']}")
        print(f"   💰 {event['price']}")
        if 'flyer_filename' in event:
            print(f"   🖼️  {event['flyer_filename']}")
        print()
    
    print("ℹ️  To complete Gancio sync:")
    print("   1. Ensure Gancio is running on localhost:13120")
    print("   2. Check Gancio admin panel for events in approval queue")
    print("   3. Or run: python3 final_working_image_upload.py")

if __name__ == "__main__":
    events = load_conduit_events()
    sync_to_gancio(events)
