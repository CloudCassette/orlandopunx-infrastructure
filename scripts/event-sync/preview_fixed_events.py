#!/usr/bin/env python3
"""
Preview what events the FIXED scraper would submit to Gancio
"""

import sys
import os

# Add current directory to path to import our fixed scraper
sys.path.append('.')

try:
    # Import our enhanced scraper (module name without .py)
    import enhanced_multi_venue_sync_fixed as scraper
    
    print("🎯 PREVIEWING FIXED SCRAPER RESULTS")
    print("="*50)
    
    # Run the fixed scraper
    willspub_events = scraper.scrape_willspub_events()
    stardust_events = scraper.scrape_stardust_events()
    
    all_events = willspub_events + stardust_events
    
    print(f"\n📊 SUMMARY:")
    print(f"🎸 Will's Pub: {len(willspub_events)} events")
    print(f"🌟 Stardust: {len(stardust_events)} events") 
    print(f"📅 Total: {len(all_events)} events")
    
    print(f"\n📋 EVENTS THAT WOULD BE SUBMITTED TO GANCIO:")
    print("="*60)
    
    for i, event in enumerate(all_events, 1):
        print(f"\n{i:2d}. {event['title']}")
        print(f"    📅 Date: {event['date']}")
        print(f"    🕐 Time: {event['time']}")
        print(f"    📍 Venue: {event['venue']}")
        print(f"    🔗 URL: {event['url']}")
        if event.get('flyer_file'):
            print(f"    🖼️  Flyer: {event['flyer_file']}")
    
    print(f"\n✨ READY FOR GANCIO SYNC!")
    print(f"Run 'python3 sync_to_gancio_fixed.py' to submit these events")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure enhanced_multi_venue_sync_fixed.py exists")
except Exception as e:
    print(f"❌ Error: {e}")

