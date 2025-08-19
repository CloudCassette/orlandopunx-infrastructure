#!/usr/bin/env python3
"""
🤖 Automated Orlando Punk Events Sync - WITH IMAGE UPLOADS
============================================================
Enhanced version that uploads flyer images with events to Gancio
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

class GancioSyncWithImages:
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
            
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data)
            
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

    def create_event_with_image(self, event_data):
        """Create event in Gancio with image upload using form submission"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False
            
        # Convert date/time to timestamp
        try:
            event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
            start_timestamp = int(event_datetime.timestamp())
        except:
            print(f"   ❌ Invalid date/time format")
            return False
        
        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later
        
        # Get place ID (Will's Pub = 1)
        place_id = 1 if event_data['venue'] == "Will's Pub" else None
        
        # Build event form data (matching the HTML form structure)
        form_data = {
            'title': event_data['title'],
            'description': event_data.get('description', ''),
            'start_datetime': str(start_timestamp),
            'end_datetime': str(end_timestamp),
            'placeId': str(place_id) if place_id else '',
            'tags': '["willspub", "live-music", "orlando"]'
        }
        
        # Prepare files for upload
        files = {}
        flyer_path = event_data.get('flyer_path')
        
        if flyer_path and os.path.exists(flyer_path):
            try:
                # Open image file for upload
                img_file = open(flyer_path, 'rb')
                files['image'] = (os.path.basename(flyer_path), img_file, 'image/jpeg')
                print(f"   🖼️  Uploading flyer: {os.path.basename(flyer_path)}")
            except Exception as e:
                print(f"   ⚠️  Could not open flyer: {e}")
        
        try:
            # Submit form with image using /add endpoint
            response = self.session.post(
                f"{self.gancio_base_url}/add",
                data=form_data,
                files=files,
                timeout=30
            )
            
            # Close file if it was opened
            if files and 'image' in files:
                files['image'][1].close()
            
            if response.status_code == 200:
                # Check if response indicates success or shows the form again
                if 'Nuovo evento' not in response.text:  # If not showing the "new event" form again
                    print(f"   ✅ {event_data['title']}")
                    return True
                else:
                    print(f"   ⚠️  Form submission returned form page (check validation)")
                    return False
            else:
                print(f"   ❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Close file if it was opened
            if files and 'image' in files:
                files['image'][1].close()
            return False

    def get_current_events(self):
        """Get current events from Gancio"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

def main():
    print("🤖 AUTOMATED ORLANDO PUNK EVENTS SYNC")
    print("=" * 50)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize sync
    sync = GancioSyncWithImages()
    
    # Authenticate
    if not sync.authenticate():
        sys.exit(1)
    
    # Scrape events
    print("📥 Scraping events with FIXED scraper...")
    events = scrape_willspub_events()
    
    if not events:
        print("❌ No events found from scraper")
        sys.exit(1)
    
    print(f"📋 Found {len(events)} events from scraper")
    
    # Get current events to avoid duplicates
    current_events = sync.get_current_events()
    current_titles = [e.get('title', '') for e in current_events]
    
    print(f"📊 Current Gancio events: {len(current_events)}")
    
    # Filter out existing events
    new_events = []
    existing_count = 0
    
    for event in events:
        if event['title'] not in current_titles:
            new_events.append(event)
        else:
            existing_count += 1
    
    print(f"🆕 New events to sync: {len(new_events)}")
    print(f"♻️  Existing events skipped: {existing_count}")
    
    if not new_events:
        print("✨ No new events to sync")
        return
    
    # Submit new events with images
    print(f"🚀 Submitting {len(new_events)} new events...")
    success_count = 0
    
    for event in new_events:
        if sync.create_event_with_image(event):
            success_count += 1
    
    print(f"✨ Sync complete: {success_count}/{len(new_events)} events submitted")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
