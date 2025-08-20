#!/usr/bin/env python3
"""
🎸 Conduit FL Manual Import for Gancio
=====================================
Creates formatted files for easy manual import of Conduit events into Gancio
"""

import json
import os
from datetime import datetime

def load_conduit_events():
    """Load Conduit events from JSON file"""
    try:
        with open('conduit_events.json', 'r') as f:
            events = json.load(f)
        print(f"📋 Loaded {len(events)} Conduit events")
        return events
    except FileNotFoundError:
        print("❌ conduit_events.json not found. Run conduit_scraper.py first.")
        return []

def create_import_files(events):
    """Create formatted import files for manual Gancio import"""
    if not events:
        print("📭 No events to process")
        return
    
    # Create import directory
    import_dir = "conduit_imports"
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)
    
    # Create individual event files
    for i, event in enumerate(events):
        filename = f"{import_dir}/conduit_event_{i+1:02d}_{event['date']}_{event['title'][:30].replace(' ', '_').replace('/', '_')}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"CONDUIT EVENT #{i+1}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Title: {event['title']}\n")
            f.write(f"Date: {event['date']}\n")
            f.write(f"Time: {event['time']}\n")
            f.write(f"Venue: {event['venue']}\n")
            f.write(f"Price: {event['price']}\n")
            f.write(f"Age: {event['age_restriction']}\n")
            f.write(f"URL: {event['url']}\n")
            
            if 'flyer_filename' in event:
                f.write(f"Flyer: flyers/{event['flyer_filename']}\n")
            if 'flyer_url' in event:
                f.write(f"Flyer URL: {event['flyer_url']}\n")
            
            f.write(f"\nDescription:\n{event['description']}\n")
            f.write(f"\nTags: conduit, live-music, orlando\n")
    
    # Create summary file
    summary_file = f"{import_dir}/conduit_import_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"CONDUIT FL EVENTS - GANCIO IMPORT SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Events: {len(events)}\n\n")
        
        f.write("QUICK COPY/PASTE FORMAT:\n")
        f.write("-" * 25 + "\n\n")
        
        for event in events:
            f.write(f"Title: {event['title']}\n")
            f.write(f"Date: {event['date']} {event['time']}\n")
            f.write(f"Venue: Conduit\n")
            f.write(f"Description: {event['description']}\n")
            if 'flyer_filename' in event:
                f.write(f"Image: flyers/{event['flyer_filename']}\n")
            f.write(f"Tags: conduit, live-music, orlando\n")
            f.write("\n" + "-" * 30 + "\n\n")
    
    print(f"📁 Created {len(events)} individual event files in {import_dir}/")
    print(f"📋 Created summary file: {summary_file}")
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Open Gancio admin panel")
    print(f"2. Go to 'Add Event' section")
    print(f"3. Copy/paste event details from the files in {import_dir}/")
    print(f"4. Upload flyer images from flyers/ directory")

if __name__ == "__main__":
    events = load_conduit_events()
    create_import_files(events)
