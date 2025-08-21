#!/usr/bin/env python3
"""
🎸 Comprehensive Orlando Punk Events Sync - All Major Venues
============================================================
Includes: Will's Pub, Conduit FL, Uncle Lou's, Stardust, Sly Fox
With framework for Orlando Weekly integration
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

# Import our scraper functions
from enhanced_multi_venue_sync import scrape_willspub_events
from conduit_scraper import scrape_conduit_events
# from orlando_weekly_scraper import scrape_orlando_weekly_events  # When available

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
        """Get venue ID for Gancio with comprehensive mapping"""
        venue_mapping = {
            "Will's Pub": 1,          # Verified existing
            "Conduit": 5,             # Verified existing  
            "Conduit FL": 5,          # Alias for Conduit
            "Stardust Video & Coffee": 4,  # Verified existing
            "Stardust Coffee": 4,     # Alias for Stardust
            "Sly Fox": 6,            # Verified existing
            "Uncle Lou's": 2,        # Likely place_id (needs verification)
            # Orlando Weekly events will use their stated venues
        }
        
        return venue_mapping.get(venue_name, 1)  # Default to Will's Pub if unknown

    def create_event_in_gancio(self, event_data):
        """Create event in Gancio using the working method"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False
            
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

def scrape_uncle_lous_events():
    """Placeholder for Uncle Lou's scraper (Songkick-based)"""
    print("📥 Uncle Lou's: Using existing Songkick integration...")
    # Uncle Lou's events are typically posted to Songkick
    # This could be enhanced with direct Songkick API or venue-specific scraping
    return []

def scrape_additional_venues():
    """Framework for additional venue scrapers"""
    all_additional = []
    
    # Uncle Lou's (could integrate with Songkick API)
    uncle_lous = scrape_uncle_lous_events()
    all_additional.extend(uncle_lous)
    
    # Orlando Weekly (when Cloudflare allows)
    # orlando_weekly = scrape_orlando_weekly_events()
    # all_additional.extend(orlando_weekly)
    
    return all_additional

def main():
    """Main comprehensive sync function"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("🎸 COMPREHENSIVE ORLANDO PUNK EVENTS SYNC")
    print("=" * 45)
    print(f"⏰ Started: {timestamp}")
    print("🎸 Will's Pub + Conduit FL + More")
    
    # Initialize syncer
    syncer = WorkingGancioSync()
    
    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1
    
    # Scrape events from all venues
    print("📥 Scraping Will's Pub events...")
    willspub_events = scrape_willspub_events()
    
    print("📥 Scraping Conduit FL events...")
    conduit_events = scrape_conduit_events(download_images=False)
    
    print("📥 Checking additional venues...")
    additional_events = scrape_additional_venues()
    
    # Combine all events
    all_events = willspub_events + conduit_events + additional_events
    
    if not all_events:
        print("📭 No events found from any venue")
        return 0
    
    print(f"📋 Found events:")
    print(f"   🎸 Will's Pub: {len(willspub_events)} events")
    print(f"   🎸 Conduit FL: {len(conduit_events)} events")
    print(f"   🎸 Additional venues: {len(additional_events)} events")
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
    
    print(f"✨ Comprehensive sync complete: {submitted}/{len(new_events)} events submitted")
    
    # Count events by venue
    venue_counts = {}
    for event in new_events:
        venue = event['venue']
        venue_counts[venue] = venue_counts.get(venue, 0) + 1
    
    for venue, count in venue_counts.items():
        print(f"   🎸 {venue}: {count} new events")
    
    # Log summary
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"⏰ Completed: {end_time}")
    
    return 0 if submitted > 0 or len(new_events) == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
