#!/usr/bin/env python3
"""
Automated Will's Pub to Gancio Sync
Automatically checks for new events and adds them to Gancio
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

class AutoWillsPubSync:
    def __init__(self):
        self.willspub_url = "https://willspub.org"
        self.gancio_url = "http://localhost:13120"
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        
    def scrape_willspub_events(self, limit=20):
        """Scrape events from Will's Pub website"""
        try:
            print(f"🎸 Scraping events from {self.willspub_url}...")
            response = self.session.get(self.willspub_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Look for event scripts or data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'EventData' in script.string:
                    # Extract event data from JavaScript
                    lines = script.string.split('\n')
                    for line in lines:
                        if 'EventData.events.push' in line and '"type" : "event"' in line:
                            # Parse event data from the line
                            try:
                                value_match = re.search(r'"value" : "([^"]+)"', line)
                                display_match = re.search(r'"display" : "([^"]+)"', line)
                                url_match = re.search(r'"url" : "([^"]+)"', line)
                                
                                if all([value_match, display_match, url_match]):
                                    display = display_match.group(1).replace('&amp;', '&').replace('&#039;', "'")
                                    url = url_match.group(1)
                                    
                                    # Parse date from display
                                    date_match = re.search(r'(\d{2}/\d{2})$', display)
                                    if date_match:
                                        title = display[:-6].strip()
                                        date_str = date_match.group(1)
                                        
                                        # Convert MM/DD to full date
                                        month, day = date_str.split('/')
                                        current_year = datetime.now().year
                                        event_date = f"2025-{month.zfill(2)}-{day.zfill(2)}"
                                        
                                        events.append({
                                            'title': title,
                                            'date': event_date,
                                            'time': '19:00',  # Default time
                                            'venue': "Will's Pub",
                                            'url': url,
                                            'description': f"Live music event at Will's Pub\\n\\nSource: {url}"
                                        })
                                        
                                        if len(events) >= limit:
                                            break
                            except Exception as e:
                                print(f"⚠️ Error parsing event: {e}")
                                continue
            
            print(f"✅ Found {len(events)} events")
            return events
            
        except Exception as e:
            print(f"❌ Error scraping Will's Pub: {e}")
            return []
    
    def get_existing_gancio_events(self):
        """Get existing events from Gancio to avoid duplicates"""
        try:
            response = self.session.get(f"{self.gancio_url}/api/events")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"⚠️ Could not fetch existing Gancio events: {e}")
            return []
    
    def sync_events(self):
        """Main sync function"""
        print("🎸 Starting Will's Pub to OrlandoPunx.com sync...")
        
        # Scrape new events
        new_events = self.scrape_willspub_events()
        if not new_events:
            print("❌ No events found, exiting")
            return False
        
        # Get existing events to check for duplicates
        existing_events = self.get_existing_gancio_events()
        existing_titles = {event.get('title', '').lower() for event in existing_events}
        
        # Filter out duplicates
        unique_events = []
        for event in new_events:
            if event['title'].lower() not in existing_titles:
                unique_events.append(event)
        
        print(f"📊 Found {len(unique_events)} new events (filtered {len(new_events) - len(unique_events)} duplicates)")
        
        # Save results
        with open('willspub_events.json', 'w') as f:
            json.dump(new_events, f, indent=2)
            
        with open('willspub_new_events.json', 'w') as f:
            json.dump(unique_events, f, indent=2)
        
        # Generate summary
        with open('sync_summary.txt', 'w') as f:
            f.write(f"Will's Pub Sync Summary - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total events scraped: {len(new_events)}\n")
            f.write(f"New events found: {len(unique_events)}\n")
            f.write(f"Duplicates filtered: {len(new_events) - len(unique_events)}\n\n")
            
            if unique_events:
                f.write("NEW EVENTS TO REVIEW:\n")
                f.write("-" * 30 + "\n")
                for i, event in enumerate(unique_events, 1):
                    f.write(f"{i}. {event['title']}\n")
                    f.write(f"   Date: {event['date']}\n")
                    f.write(f"   URL: {event['url']}\n\n")
        
        return len(unique_events) > 0

if __name__ == "__main__":
    syncer = AutoWillsPubSync()
    has_new_events = syncer.sync_events()
    
    if has_new_events:
        print("🎯 New events found! Check sync_summary.txt for details")
        sys.exit(0)  # Success
    else:
        print("ℹ️ No new events found")
        sys.exit(0)  # Still success, just no new events
