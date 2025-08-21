#!/usr/bin/env python3
"""
🎸 Sync Conduit Events with CORRECT Place ID
===========================================
Syncs Conduit events using the correct place_id (5, not 3)
"""

import json
import requests
import os
import getpass
from datetime import datetime

class ConduitGancioSync:
    def __init__(self, gancio_url="https://orlandopunx.com"):
        self.gancio_base_url = gancio_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.authenticated = False

    def authenticate(self, email=None, password=None):
        """Authenticate with Gancio"""
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
                print("✅ Authentication successful!")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def submit_event(self, event_data):
        """Submit single event to Gancio"""
        if not self.authenticated:
            print("❌ Not authenticated")
            return False
        
        # Use CORRECT Conduit place_id (5)
        gancio_event = {
            "title": event_data['title'],
            "start_datetime": f"{event_data['date']} {event_data['time']}:00",
            "end_datetime": f"{event_data['date']} 23:59:00",  # Default end time
            "place_id": 5,  # CORRECT Conduit ID!
            "tags": ["music", "live"],
            "description": event_data.get('description', ''),
        }
        
        # Add URL if available
        if event_data.get('url'):
            gancio_event['url'] = event_data['url']
        
        try:
            response = self.session.post(f"{self.gancio_base_url}/add", json=gancio_event)
            
            if response.status_code == 200:
                print(f"   ✅ Event submitted: {event_data['title']}")
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
    print("🎵 Syncing Conduit events with CORRECT place_id (5)")
    print("=" * 55)
    
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
    sync = ConduitGancioSync()
    
    if not sync.authenticate():
        print("❌ Authentication failed")
        return
    
    print(f"🔄 Submitting {len(future_events)} events with place_id=5...")
    
    # Submit events
    submitted = 0
    failed = 0
    
    for event in future_events:
        if sync.submit_event(event):
            submitted += 1
        else:
            failed += 1
    
    print(f"\n📊 SYNC RESULTS:")
    print(f"   ✅ Submitted: {submitted} events") 
    print(f"   ❌ Failed: {failed} events")
    print(f"\n📋 Next steps:")
    print(f"   1. Check https://orlandopunx.com for new Conduit events")
    print(f"   2. Go to admin panel if available for approval")

if __name__ == "__main__":
    main()
