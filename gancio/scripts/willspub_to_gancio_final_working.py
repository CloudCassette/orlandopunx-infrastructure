#!/usr/bin/env python3
"""
Will's Pub to Gancio Sync - FINAL WORKING VERSION
Creates events that go to approval queue for manual review
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
import getpass

class WillsPubGancioSync:
    def __init__(self, gancio_base_url):
        self.willspub_url = "https://willspub.org"
        self.gancio_base_url = gancio_base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set proper headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json'
        })
        
        # Known place IDs from Gancio
        self.places = {
            "Will's Pub": 1,
            "Uncle Lou's": 2,
            "Lil' Indies": 1  # Assume same as Will's Pub for now
        }
        
        self.authenticated = False
    
    def authenticate(self):
        """Authenticate with Gancio"""
        print("🔑 Gancio Authentication")
        
        email = input("Enter your Gancio email: ").strip()
        if not email:
            return False
            
        password = getpass.getpass("Enter your password: ").strip()
        if not password:
            return False
        
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
    
    def scrape_events(self, limit=None):
        """Scrape events from Will's Pub"""
        try:
            print(f"📥 Scraping events from Will's Pub...")
            response = self.session.get(self.willspub_url, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            if 'EventData' not in content:
                print("❌ No EventData found")
                return []
            
            # Extract events from JavaScript
            events = []
            lines = content.split('\n')
            
            for line in lines:
                if 'EventData.events.push' in line and '"type" : "event"' in line:
                    try:
                        value_match = re.search(r'"value" : "([^"]+)"', line)
                        display_match = re.search(r'"display" : "([^"]+)"', line)
                        url_match = re.search(r'"url" : "([^"]+)"', line)
                        
                        if all([value_match, display_match, url_match]):
                            display = display_match.group(1).replace('&amp;', '&').replace('&#039;', "'")
                            
                            # Parse title and date
                            date_match = re.search(r'(\d{2}/\d{2})$', display)
                            if date_match:
                                title = display[:-6].strip()
                            else:
                                title = display
                            
                            events.append({
                                'title': title,
                                'url': url_match.group(1)
                            })
                            
                            if limit and len(events) >= limit:
                                break
                                
                    except Exception:
                        continue
            
            print(f"✅ Found {len(events)} events")
            
            # Get details for each event
            detailed_events = []
            for i, event in enumerate(events, 1):
                print(f"📋 [{i}/{len(events)}] Processing: {event['title']}")
                
                try:
                    details = self.scrape_event_details(event)
                    if details:
                        detailed_events.append(details)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
            
            return detailed_events
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []
    
    def scrape_event_details(self, event):
        """Get detailed info for an event"""
        try:
            response = self.session.get(event['url'], timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {
                'title': event['title'],
                'source_url': event['url']
            }
            
            # Extract event details
            date_elem = soup.find('span', class_='tw-event-date')
            if date_elem:
                date_str = date_elem.text.strip()
                details['date_string'] = date_str
                details['start_date'] = self.parse_date(date_str)
                print(f"   📅 {date_str} -> {details['start_date']}")
            
            time_elem = soup.find('span', class_='tw-event-door-time')
            if time_elem:
                time_str = time_elem.text.strip()
                details['start_time'] = self.parse_time(time_str)
                print(f"   🕐 {time_str} -> {details['start_time']}")
            else:
                details['start_time'] = "19:00"
            
            venue_elem = soup.find('span', class_='tw-venue-name')
            if venue_elem:
                details['venue'] = venue_elem.text.strip()
                print(f"   📍 {details['venue']}")
            else:
                details['venue'] = "Will's Pub"
            
            desc_elem = soup.find('div', class_='event-description')
            if desc_elem:
                details['description'] = desc_elem.get_text().strip()[:500]
            
            price_elem = soup.find('span', class_='tw-price')
            if price_elem:
                details['price'] = price_elem.text.strip()
                print(f"   💰 {details['price']}")
            
            return details
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD"""
        try:
            date_str = re.sub(r'\s+', ' ', date_str.strip())
            
            formats = [
                "%b %d, %Y",        # Aug 10, 2025
                "%a %b, %d %Y",     # Sun Aug, 10 2025
                "%a %b %d, %Y",     # Sun Aug 10, 2025  
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def parse_time(self, time_str):
        """Parse time string to HH:MM"""
        try:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*([AP]M)', time_str, re.I)
            if time_match:
                hour, minute, ampm = time_match.groups()
                hour = int(hour)
                minute = int(minute)
                
                if ampm.upper() == 'PM' and hour != 12:
                    hour += 12
                elif ampm.upper() == 'AM' and hour == 12:
                    hour = 0
                
                return f"{hour:02d}:{minute:02d}"
            
            return "19:00"
        except Exception:
            return "19:00"
    
    def convert_to_timestamp(self, event_data):
        """Convert to timestamp"""
        if not event_data.get('start_date') or not event_data.get('start_time'):
            return None
            
        try:
            datetime_str = f"{event_data['start_date']} {event_data['start_time']}"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            return int(dt.timestamp())
        except ValueError:
            return None
    
    def create_event_in_gancio(self, event_data):
        """Create event in Gancio (goes to approval queue)"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False
            
        start_timestamp = self.convert_to_timestamp(event_data)
        if not start_timestamp:
            print("   ❌ Invalid date/time")
            return False
        
        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later
        
        # Get place ID
        venue_name = event_data.get('venue', 'Will\'s Pub')
        place_id = self.places.get(venue_name, 1)  # Default to Will's Pub
        
        # Build description
        description_parts = []
        if event_data.get('description'):
            description_parts.append(event_data['description'])
        if event_data.get('price'):
            description_parts.append(f"Price: {event_data['price']}")
        description_parts.append(f"More info: {event_data.get('source_url', '')}")
        
        # Create event data in Gancio format
        gancio_event = {
            "title": event_data.get('title', ''),
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "description": "\n\n".join(description_parts),
            "tags": ["willspub", "live-music", "orlando"],
            "placeId": place_id,
            "multidate": False
        }
        
        try:
            response = self.session.post(
                f"{self.gancio_base_url}/add",
                json=gancio_event,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ Event submitted for approval: {event_data['title']}")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_sync(self, limit=5):
        """Main sync function"""
        print("🎵 Will's Pub to Gancio Sync - FINAL VERSION")
        print("="*55)
        print("Events will be submitted to your approval queue")
        print("="*55)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
        
        # Scrape events
        events = self.scrape_events(limit=limit)
        
        if not events:
            print("❌ No events found")
            return
        
        print(f"\n✨ Found {len(events)} events to sync")
        
        # Show what will be created
        print("\n" + "="*50)
        print("EVENTS TO BE SUBMITTED:")
        print("="*50)
        
        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event.get('title', 'No title')}")
            print(f"   📅 {event.get('start_date', 'No date')} at {event.get('start_time', 'No time')}")
            print(f"   📍 {event.get('venue', 'No venue')}")
            if event.get('price'):
                print(f"   💰 {event.get('price')}")
            print(f"   🔗 {event.get('source_url', 'No URL')}")
        
        # Confirm with user
        print(f"\n" + "="*50)
        proceed = input(f"Submit these {len(events)} events to your approval queue? (y/N): ").strip().lower()
        
        if proceed != 'y':
            print("👋 No events submitted")
            return
        
        # Create events
        print(f"\n🚀 Submitting events...")
        submitted = 0
        failed = 0
        
        for i, event in enumerate(events, 1):
            print(f"\n[{i}/{len(events)}] {event.get('title', 'Unknown')}")
            if self.create_event_in_gancio(event):
                submitted += 1
            else:
                failed += 1
            time.sleep(1)
        
        print(f"\n✨ Sync Complete!")
        print(f"   ✅ Submitted: {submitted} events")
        print(f"   ❌ Failed: {failed} events")
        print(f"\n📋 Next steps:")
        print(f"   1. Go to your Gancio admin panel")
        print(f"   2. Review and approve the submitted events")
        print(f"   3. They will then appear on https://orlandopunx.com")

if __name__ == "__main__":
    import sys
    
    # Allow limiting events via command line
    limit = 5  # Default to 5 events for testing
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    
    syncer = WillsPubGancioSync("https://orlandopunx.com")
    syncer.run_sync(limit=limit)
