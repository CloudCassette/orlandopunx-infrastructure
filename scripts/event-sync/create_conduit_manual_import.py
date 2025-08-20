#!/usr/bin/env python3
"""
🎸 Create Manual Conduit Import Files
====================================
Creates manual import files for Conduit events that can be copy-pasted into Gancio
"""

import json
from datetime import datetime

def load_conduit_events():
    """Load Conduit events from JSON file"""
    try:
        with open('conduit_events.json', 'r') as f:
            events = json.load(f)
        print(f"📋 Loaded {len(events)} Conduit events")
        return events
    except FileNotFoundError:
        print("❌ conduit_events.json not found")
        return []

def create_manual_import_files(events):
    """Create manual import files for easy copy-paste"""
    if not events:
        print("📭 No events to process")
        return
    
    # Filter out past events (today or earlier)
    today = datetime.now().strftime('%Y-%m-%d')
    future_events = [e for e in events if e['date'] >= today]
    
    print(f"🔄 Processing {len(future_events)} future events...")
    
    # Create individual text files for each event
    for i, event in enumerate(future_events, 1):
        filename = f"conduit_import_{i:02d}_{event['title'].replace(' ', '_').replace('/', '-')[:50]}.txt"
        # Clean filename
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        with open(filename, 'w') as f:
            f.write(f"CONDUIT EVENT - MANUAL IMPORT #{i}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Title: {event['title']}\n")
            f.write(f"Date: {event['date']}\n")
            f.write(f"Time: {event['time']}\n")
            f.write(f"Venue: Conduit (6700 Aloma Ave)\n")
            f.write(f"Price: {event.get('price', 'TBD')}\n")
            f.write(f"Age: {event.get('age_restriction', '18+')}\n")
            f.write(f"URL: {event.get('url', '')}\n")
            
            if event.get('description'):
                f.write(f"\nDescription:\n{event['description']}\n")
            
            if event.get('flyer_filename'):
                f.write(f"\nFlyer: {event['flyer_filename']}\n")
                f.write(f"(Located in: /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/flyers/)\n")
            
            f.write(f"\nOriginal URL: {event.get('url', '')}\n")
            
        print(f"📄 Created: {filename}")
    
    # Create summary file
    with open('conduit_events_summary.txt', 'w') as f:
        f.write(f"CONDUIT EVENTS SUMMARY\n")
        f.write("=" * 30 + "\n")
        f.write(f"Total events: {len(future_events)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        for i, event in enumerate(future_events, 1):
            f.write(f"{i:2d}. {event['title']}\n")
            f.write(f"    📅 {event['date']} at {event['time']}\n")
            f.write(f"    💰 {event.get('price', 'TBD')}\n")
            if event.get('flyer_filename'):
                f.write(f"    🖼️  {event['flyer_filename']}\n")
            f.write("\n")
    
    print(f"📄 Created: conduit_events_summary.txt")
    print(f"\n✅ Manual import files created!")
    print(f"📁 Files created: {len(future_events) + 1}")
    print(f"\n📋 To import manually:")
    print(f"   1. Go to https://orlandopunx.com/admin")
    print(f"   2. Click PLACES tab and ensure 'Conduit' venue exists")
    print(f"   3. Click + button to add new events")
    print(f"   4. Copy/paste info from each .txt file")
    print(f"   5. Upload flyers from ./flyers/ directory")

if __name__ == "__main__":
    events = load_conduit_events()
    create_manual_import_files(events)
