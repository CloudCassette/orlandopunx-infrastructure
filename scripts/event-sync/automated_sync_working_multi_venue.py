#!/usr/bin/env python3
"""
🤖 Automated Orlando Punk Events Sync - Multi-Venue (Will's Pub + Conduit)
===========================================================================
Uses the same authentication method as the working willspub_to_gancio_final_working.py
Now includes both Will's Pub and Conduit FL events!
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import hashlib

# Import our fixed scraper functions
from enhanced_multi_venue_sync import scrape_willspub_events
from conduit_scraper import scrape_conduit_events

class WorkingGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        
        # Set headers like the working script
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        self.authenticated = False

    def authenticate(self):
        """Authenticate with Gancio using the WORKING method"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ Missing GANCIO_PASSWORD environment variable")
            print("💡 Make sure you added it to your .bashrc and reloaded your shell")
            return False
        
        print(f"🔑 Authenticating with Gancio as {email}...")
        
        try:
            # Use the WORKING authentication method (web form, not API)
            login_data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Authentication successful!")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_venue_id(self, venue_name):
        """Get or create venue ID for Gancio"""
        venue_mapping = {
            "Will's Pub": 1,  # Known working ID
            "Conduit FL": 5,  # We'll create this if needed
            "Conduit": 5
        }
        
        return venue_mapping.get(venue_name, 1)  # Default to Will's Pub ID if unknown

    def create_event_in_gancio(self, event_data):
        """Create event in Gancio using the working method"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False
            
        # Convert date/time to timestamp (same logic as working script)
        try:
            event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
            start_timestamp = int(event_datetime.timestamp())
        except:
            print(f"   ❌ Invalid date/time format for {event_data['title']}")
            return False
        
        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later
        
        # Get place ID based on venue
        place_id = self.get_venue_id(event_data['venue'])
        
        gancio_data = {
            'title': event_data['title'],
            'description': event_data.get('description', ''),
            'start_datetime': start_timestamp,
            'end_datetime': end_timestamp,
            'place_id': place_id,
            'tags': []
        }
        
        try:
            response = self.session.post(f"{self.gancio_base_url}/api/event", json=gancio_data)
            
            if response.status_code in [200, 201]:
                venue = event_data['venue']
                title = event_data['title']
                print(f"   ✅ {title} ({venue})")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code} - {event_data['title']}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

def main():
    """Main automated sync function with multi-venue support"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("🤖 AUTOMATED ORLANDO PUNK EVENTS SYNC (MULTI-VENUE)")
    print("="*55)
    print(f"⏰ Started: {timestamp}")
    print("🎸 Will's Pub + Conduit FL")
    
    # Initialize syncer
    syncer = WorkingGancioSync()
    
    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1
    
    # Scrape events from both venues
    print("📥 Scraping Will's Pub events...")
    willspub_events = scrape_willspub_events()
    
    print("📥 Scraping Conduit FL events...")
    conduit_events = scrape_conduit_events(download_images=False)  # Skip image downloads for now
    
    # Combine events
    all_events = willspub_events + conduit_events
    
    if not all_events:
        print("📭 No events found from any venue")
        return 0
    
    print(f"📋 Found events:")
    print(f"   🎸 Will's Pub: {len(willspub_events)} events")
    print(f"   🎸 Conduit FL: {len(conduit_events)} events")
    print(f"   📅 Total: {len(all_events)} events")
    
    # Get existing events to avoid duplicates  
    try:
        response = syncer.session.get(f"{syncer.gancio_base_url}/api/events")
        if response.status_code == 200:
            existing_events = {event['title'] for event in response.json()}
            print(f"📊 Current Gancio events: {len(existing_events)}")
        else:
            existing_events = set()
            print("⚠️  Could not fetch existing events")
    except:
        existing_events = set()
        print("⚠️  Could not fetch existing events")
    
    # Filter for new events only
    new_events = [event for event in all_events if event['title'] not in existing_events]
    
    print(f"🆕 New events to sync: {len(new_events)}")
    print(f"♻️  Existing events skipped: {len(all_events) - len(new_events)}")
    
    if not new_events:
        print("✨ All events already exist - no work to do!")
        return 0
    
    # Submit new events
    print(f"🚀 Submitting {len(new_events)} new events...")
    
    submitted = 0
    for event in new_events:
        if syncer.create_event_in_gancio(event):
            submitted += 1
    
    print(f"✨ Multi-venue sync complete: {submitted}/{len(new_events)} events submitted")
    
    # Count events by venue
    willspub_new = len([e for e in new_events if e['venue'] == "Will's Pub"])
    conduit_new = len([e for e in new_events if 'Conduit' in e['venue']])
    print(f"   🎸 Will's Pub events in batch: {willspub_new}")
    print(f"   🎸 Conduit FL events in batch: {conduit_new}")
    
    # Log summary
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"⏰ Completed: {end_time}")
    
    return 0 if submitted > 0 or len(new_events) == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
