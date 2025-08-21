#!/usr/bin/env python3
"""
🎸 FIXED Will's Pub to Gancio Sync
=================================
Uses the fixed scraper to get real event titles and syncs to Gancio
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
import getpass

# Import our fixed scraper functions
from enhanced_multi_venue_sync_fixed import main as scrape_all_venues

class FixedGancioSync:
    def __init__(self):
        self.gancio_url = "http://localhost:13120"
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        self.gancio_authenticated = False

    def authenticate_gancio(self, email=None, password=None):
        """Authenticate with Gancio"""
        print("🔑 Gancio Authentication")
        
        if not email:
            email = input("Enter your Gancio email: ")
        if not password:
            password = getpass.getpass("Enter your password: ")
        
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
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def submit_event_to_gancio(self, event):
        """Submit an event to Gancio"""
        if not self.gancio_authenticated:
            print("❌ Not authenticated with Gancio")
            return False
        
        try:
            # Convert our event format to Gancio format
            gancio_event = {
                'title': event['title'],
                'description': event.get('description', ''),
                'start_datetime': f"{event['date']}T{event['time']}:00",
                'place_name': event['venue'],
                'place_address': "1042 N. Mills Ave. Orlando, FL 32803" if event['venue'] == "Will's Pub" else "",
                'tags': ['punk'] if 'punk' in event['title'].lower() else []
            }
            
            response = self.session.post(f"{self.gancio_url}/api/events", json=gancio_event)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Event submitted for approval: {event['title']}")
                return True
            else:
                print(f"   ❌ Failed to submit {event['title']}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error submitting {event['title']}: {e}")
            return False

def main():
    """Main sync function"""
    print("🎵 FIXED Will's Pub to Gancio Sync")
    print("="*50)
    print("Events will be submitted to your approval queue")
    print("="*50)
    
    # Initialize syncer
    syncer = FixedGancioSync()
    
    # Authenticate
    if not syncer.authenticate_gancio():
        print("❌ Authentication failed. Exiting.")
        return
    
    # Scrape events using our fixed scraper
    print("📥 Scraping events from Will's Pub...")
    events = scrape_all_venues()
    
    if not events:
        print("📭 No events found to sync")
        return
    
    print(f"✅ Found {len(events)} events")
    
    # Show preview
    print("\n" + "="*50)
    print("EVENTS TO BE SUBMITTED:")
    print("="*50)
    
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   📅 {event['date']} at {event['time']}")
        print(f"   📍 {event['venue']}")
        print(f"   🔗 {event['url']}")
    
    # Confirm submission
    print("\n" + "="*50)
    confirm = input(f"Submit these {len(events)} events to your approval queue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("❌ Sync cancelled")
        return
    
    print("\n🚀 Submitting events...")
    
    submitted = 0
    failed = 0
    
    for i, event in enumerate(events, 1):
        print(f"\n[{i}/{len(events)}] {event['title']}")
        
        if syncer.submit_event_to_gancio(event):
            submitted += 1
        else:
            failed += 1
    
    print(f"\n✨ Sync Complete!")
    print(f"   ✅ Submitted: {submitted} events")
    print(f"   ❌ Failed: {failed} events")
    
    if submitted > 0:
        print(f"\n📋 Next steps:")
        print(f"   1. Go to your Gancio admin panel")
        print(f"   2. Review and approve the submitted events")
        print(f"   3. They will then appear on https://orlandopunx.com")

if __name__ == "__main__":
    main()
