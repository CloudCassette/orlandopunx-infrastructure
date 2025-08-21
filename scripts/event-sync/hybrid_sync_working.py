#!/usr/bin/env python3
"""
🔀 Hybrid Automated Orlando Punk Events Sync
==============================================
Maintains backward compatibility while supporting new modular structure.
Can use either old or new scraper modules seamlessly.
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

class HybridWorkingGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        
        # Set headers like the working script
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        self.authenticated = False

    def get_scraper_function(self):
        """Get scraper function from either old or new location"""
        
        # Try new modular scraper first
        try:
            # Add project root to path for importing from src/
            project_root = os.path.join(os.path.dirname(__file__), '../../')
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from src.scrapers.willspub import scrape_willspub_events
            print("🔄 Using NEW modular scraper from src/scrapers/")
            return scrape_willspub_events
            
        except ImportError:
            print("📦 New scraper not available, falling back to legacy")
            
        # Fallback to old scraper
        try:
            from enhanced_multi_venue_sync import scrape_willspub_events
            print("🔄 Using LEGACY scraper (enhanced_multi_venue_sync)")
            return scrape_willspub_events
            
        except ImportError:
            raise ImportError("❌ No scraper available (neither new nor legacy)")

    def authenticate(self):
        """Authenticate with Gancio using the WORKING method"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ Missing GANCIO_PASSWORD environment variable")
            return False
        
        print(f"🔑 Authenticating with Gancio as {email}...")
        
        try:
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

    def create_event_in_gancio(self, event_data):
        """Create event in Gancio using the working method"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False
            
        try:
            event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
            start_timestamp = int(event_datetime.timestamp())
        except:
            print(f"   ❌ Invalid date/time format")
            return False
        
        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later
        place_id = 1 if event_data['venue'] == "Will's Pub" else None
        
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
                print(f"   ✅ {event_data['title']}")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

def main():
    """Main automated sync function with hybrid scraper support"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("🔀 HYBRID AUTOMATED ORLANDO PUNK EVENTS SYNC")
    print("="*55)
    print(f"⏰ Started: {timestamp}")
    print("🔄 Supports both legacy and new modular scrapers")
    
    # Initialize syncer
    syncer = HybridWorkingGancioSync()
    
    # Get scraper function (new or old)
    try:
        scrape_willspub_events = syncer.get_scraper_function()
    except ImportError as e:
        print(f"❌ {e}")
        return 1
    
    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1
    
    # Scrape events
    print("📥 Scraping events...")
    events = scrape_willspub_events()
    
    if not events:
        print("📭 No events found")
        return 0
    
    print(f"📋 Found {len(events)} events from scraper")
    
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
    new_events = [event for event in events if event['title'] not in existing_events]
    
    print(f"🆕 New events to sync: {len(new_events)}")
    print(f"♻️  Existing events skipped: {len(events) - len(new_events)}")
    
    if not new_events:
        print("✨ All events already exist - no work to do!")
        return 0
    
    # Submit new events
    print(f"🚀 Submitting {len(new_events)} new events...")
    
    submitted = 0
    for event in new_events:
        if syncer.create_event_in_gancio(event):
            submitted += 1
    
    print(f"✨ Sync complete: {submitted}/{len(new_events)} events submitted")
    
    # Log summary
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"⏰ Completed: {end_time}")
    
    return 0 if submitted > 0 or len(new_events) == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
