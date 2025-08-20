#!/usr/bin/env python3
"""
🎸 Sync Conduit Events to Local Gancio
=====================================
Syncs Conduit events to local Gancio instance (like Will's Pub sync)
"""

import json
import requests
import os
import getpass
from datetime import datetime
import time as time_module

class ConduitLocalGancioSync:
    def __init__(self, gancio_url="http://localhost:13120"):
        self.gancio_base_url = gancio_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.authenticated = False

    def authenticate(self, email=None, password=None):
        """Authenticate with local Gancio"""
        if not email:
            email = "godlessamericarecords@gmail.com"
        
        if not password:
            password = os.environ.get('GANCIO_PASSWORD')
            if not password:
                password = getpass.getpass("Enter your Gancio password: ")
            else:
                print(f"📧 Using email: {email}")
                print("🔑 Using password from environment")
        
        login_data = {
            'email': email,
            'password': password
        }
        
        try:
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Authentication successful with LOCAL Gancio!")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def submit_event(self, event_data):
        """Submit single event to local Gancio"""
        if not self.authenticated:
            print("❌ Not authenticated")
            return False
        
        # Parse datetime to timestamp (like Will's Pub sync)
        event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
        start_timestamp = int(event_datetime.timestamp())
        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later
        
        # Use Will's Pub format for local Gancio
        gancio_event = {
            "title": event_data['title'],
            "start_datetime": start_timestamp,  # Numeric timestamp
            "end_datetime": end_timestamp,      # Numeric timestamp
            "description": event_data.get('description', ''),
            "tags": ["conduit", "live-music", "orlando"],  # Similar to Will's Pub tags
            "placeId": 5,  # Conduit venue ID
            "multidate": False
        }
        
        # Add URL if available
        if event_data.get('url'):
            gancio_event['url'] = event_data['url']
        
        try:
            response = self.session.post(f"{self.gancio_base_url}/add", json=gancio_event)
            
            if response.status_code == 200:
                print(f"   ✅ Event submitted to LOCAL queue: {event_data['title']}")
                return True
            else:
                print(f"   ❌ Failed to submit {event_data['title']}: {response.status_code}")
                print(f"      Response: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error submitting {event_data['title']}: {e}")
            return False

def main():
    """Main sync function"""
    print("🎵 Syncing Conduit events to LOCAL Gancio (localhost:13120)")
    print("=" * 65)
    print("🏗️ This matches the Will's Pub sync workflow!")
    
    # Load events
    try:
        with open('conduit_events.json', 'r') as f:
            events = json.load(f)
        print(f"📋 Loaded {len(events)} events from conduit_events.json")
    except FileNotFoundError:
        print("❌ conduit_events.json not found")
        return
    
    # Filter future events
    today = datetime.now().strftime('%Y-%m-%d')
    future_events = [e for e in events if e['date'] >= today]
    print(f"📅 {len(future_events)} future events to sync")
    
    # Initialize sync
    sync = ConduitLocalGancioSync()
    
    if not sync.authenticate():
        print("❌ Authentication failed")
        return
    
    print(f"🔄 Submitting {len(future_events)} events to LOCAL Gancio approval queue...")
    
    # Submit events
    submitted = 0
    failed = 0
    
    for event in future_events:
        if sync.submit_event(event):
            submitted += 1
        else:
            failed += 1
    
    print(f"\n📊 SYNC RESULTS:")
    print(f"   ✅ Submitted to LOCAL queue: {submitted} events") 
    print(f"   ❌ Failed: {failed} events")
    print(f"\n📋 Next steps:")
    print(f"   1. Check your LOCAL admin panel at http://localhost:13120/admin")
    print(f"   2. Review and approve the Conduit events")
    print(f"   3. Events will then sync to https://orlandopunx.com")

if __name__ == "__main__":
    main()
