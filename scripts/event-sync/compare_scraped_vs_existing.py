#!/usr/bin/env python3
"""
Compare what we scraped vs what's in Gancio to find NEW events
"""

import requests
import json
from datetime import datetime

def compare_events():
    print("🔍 COMPARING SCRAPED VS EXISTING EVENTS")
    print("="*50)
    
    # Load scraped events
    try:
        with open('combined_events_fixed.json', 'r') as f:
            scraped_events = json.load(f)
        print(f"📥 Scraped events: {len(scraped_events)}")
    except Exception as e:
        print(f"❌ Error loading scraped events: {e}")
        return
    
    # Get current Gancio events
    try:
        response = requests.get("http://localhost:13120/api/events")
        if response.status_code == 200:
            gancio_events = response.json()
            print(f"📋 Gancio events: {len(gancio_events)}")
        else:
            print(f"❌ Failed to get Gancio events: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting Gancio events: {e}")
        return
    
    # Create lookup of existing event titles
    existing_titles = {event['title'] for event in gancio_events}
    
    # Find new events
    new_events = []
    existing_count = 0
    
    for event in scraped_events:
        if event['title'] not in existing_titles:
            new_events.append(event)
        else:
            existing_count += 1
    
    print(f"✅ Found {len(new_events)} NEW events to test with")
    print(f"📋 {existing_count} events already exist in Gancio")
    print()
    
    if new_events:
        print("🆕 NEW EVENTS TO SYNC:")
        print("="*40)
        for i, event in enumerate(new_events, 1):
            print(f"{i:2d}. {event['title']}")
            print(f"    📅 {event['date']} at {event['time']}")
            print(f"    🔗 {event['url']}")
            print()
            
        # Save new events for testing
        with open('new_events_to_test.json', 'w') as f:
            json.dump(new_events, f, indent=2)
        print(f"💾 Saved {len(new_events)} new events to new_events_to_test.json")
        
    else:
        print("📭 No new events found - all scraped events already exist in Gancio")
        print("💡 This means the scraping and sync is working correctly!")
    
    print()
    print("🎯 READY FOR REAL TEST!")
    print("We can now sync these new events to test the full pipeline.")

if __name__ == "__main__":
    compare_events()
