#!/usr/bin/env python3
"""
🔍 Analyze Existing Conduit Event
=================================
Examines the existing Conduit event to understand correct venue format
"""

import requests
import json

def analyze_conduit_event():
    """Analyze the existing Conduit event"""
    
    print("🔍 Analyzing existing Conduit event...")
    
    events_response = requests.get("https://orlandopunx.com/api/events")
    
    if events_response.status_code == 200:
        events_data = events_response.json()
        print(f"📊 Found {len(events_data)} events")
        
        # Find Conduit events
        conduit_events = []
        for event in events_data:
            place_name = event.get('place', {}).get('name', '')
            if 'conduit' in place_name.lower():
                conduit_events.append(event)
        
        print(f"🎸 Found {len(conduit_events)} Conduit events")
        
        if conduit_events:
            print(f"\n📝 Existing Conduit event details:")
            event = conduit_events[0]
            
            print(f"Full event JSON:")
            print(json.dumps(event, indent=2))
            
            # Extract key venue info
            place_info = event.get('place', {})
            print(f"\n🏢 Venue Information:")
            print(f"   • ID: {place_info.get('id')}")
            print(f"   • Name: {place_info.get('name')}")
            print(f"   • Address: {place_info.get('address')}")
            print(f"   • place_id field: {event.get('place_id')}")
            
        else:
            print("❌ No Conduit events found")
            
            # Show all venues for reference
            print(f"\n📊 All venues in existing events:")
            venues = set()
            for event in events_data:
                place_info = event.get('place', {})
                venue_name = place_info.get('name', 'Unknown')
                venue_id = place_info.get('id', 'unknown')
                venues.add(f"ID {venue_id}: {venue_name}")
            
            for venue in sorted(venues):
                print(f"   • {venue}")

if __name__ == "__main__":
    analyze_conduit_event()
