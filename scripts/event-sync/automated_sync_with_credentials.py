#!/usr/bin/env python3
"""
🎸 Automated Will's Pub to Gancio Sync with Environment Variables
===============================================================
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our fixed scraper functions
from enhanced_multi_venue_sync import scrape_willspub_events

class AutomatedGancioSync:
    def __init__(self):
        self.gancio_url = os.getenv('GANCIO_URL', 'http://localhost:13120')
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        self.gancio_authenticated = False

    def authenticate_gancio(self):
        """Authenticate with Gancio using environment variables"""
        email = os.getenv('GANCIO_EMAIL')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not email or not password:
            print("❌ Missing GANCIO_EMAIL or GANCIO_PASSWORD environment variables")
            print("💡 Set them with:")
            print("   export GANCIO_EMAIL='your-email@example.com'")
            print("   export GANCIO_PASSWORD='your-password'")
            return False
        
        print(f"🔑 Authenticating with Gancio as {email}...")
        
        try:
            # Login to Gancio
            login_data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(f"{self.gancio_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                print("✅ Authentication successful!")
                self.gancio_authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                if response.text:
                    print(f"Error details: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_all_events_with_status(self):
        """Get all events including their approval status"""
        try:
            # Try different endpoints to find pending events
            endpoints = [
                "/api/events",
                "/api/events?status=pending", 
                "/api/events?status=draft",
                "/api/events/admin"
            ]
            
            all_events = {}
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.gancio_url}{endpoint}")
                    if response.status_code == 200:
                        events = response.json()
                        print(f"📋 Found {len(events)} events at {endpoint}")
                        for event in events:
                            all_events[event['title']] = {
                                'event': event,
                                'source': endpoint
                            }
                except:
                    continue
            
            return all_events
            
        except Exception as e:
            print(f"⚠️  Could not fetch events: {e}")
            return {}

    def submit_event_to_gancio(self, event):
        """Submit an event to Gancio"""
        if not self.gancio_authenticated:
            print("❌ Not authenticated with Gancio")
            return False
        
        try:
            # Convert our event format to Gancio format
            start_datetime = f"{event['date']}T{event['time']}:00"
            
            gancio_event = {
                'title': event['title'],
                'description': event.get('description', f"Event at {event['venue']}"),
                'start_datetime': start_datetime,
                'place_name': event['venue'],
                'place_address': "1042 N. Mills Ave. Orlando, FL 32803" if event['venue'] == "Will's Pub" else "",
                'tags': ['punk'] if any(word in event['title'].lower() for word in ['punk', 'hardcore', 'metal']) else []
            }
            
            response = self.session.post(f"{self.gancio_url}/api/events", json=gancio_event)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Event submitted: {event['title']}")
                return True
            else:
                print(f"   ❌ Failed to submit {event['title']}: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error submitting {event['title']}: {e}")
            return False

def main():
    """Main automated sync function"""
    print("🤖 AUTOMATED Will's Pub to Gancio Sync")
    print("="*50)
    
    # Initialize syncer
    syncer = AutomatedGancioSync()
    
    # Authenticate
    if not syncer.authenticate_gancio():
        return 1
    
    # Check current events status
    print("📋 Checking current Gancio events...")
    all_events = syncer.get_all_events_with_status()
    
    if all_events:
        print(f"📊 Current events in Gancio:")
        for title, info in list(all_events.items())[:5]:  # Show first 5
            event = info['event']
            source = info['source']
            print(f"   • {title} (from {source})")
            
    # Scrape events using our FIXED scraper
    print("\n📥 Scraping events from Will's Pub...")
    events = scrape_willspub_events()
    
    if not events:
        print("📭 No events found to sync")
        return 0
    
    # Filter out events that already exist
    new_events = []
    existing_count = 0
    
    for event in events:
        if event['title'] not in all_events:
            new_events.append(event)
        else:
            existing_count += 1
    
    print(f"✅ Found {len(events)} total events")
    print(f"📋 {existing_count} already exist in Gancio")
    print(f"🆕 {len(new_events)} are new")
    
    if not new_events:
        print("✨ All events are already in Gancio - no work to do!")
        return 0
    
    # Submit new events
    print(f"\n🚀 Submitting {len(new_events)} new events...")
    
    submitted = 0
    failed = 0
    
    for event in new_events:
        if syncer.submit_event_to_gancio(event):
            submitted += 1
        else:
            failed += 1
    
    print(f"\n✨ Automated Sync Complete!")
    print(f"   ✅ Submitted: {submitted} events")
    print(f"   ❌ Failed: {failed} events")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
