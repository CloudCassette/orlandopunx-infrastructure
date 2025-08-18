#!/usr/bin/env python3
"""
🌟 Stardust Coffee & Video Event Scraper
=======================================
Scrapes events from https://stardustvideoandcoffee.wordpress.com/events-2/
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import os

def scrape_stardust_events():
    """Scrape events from Stardust Coffee & Video"""
    print("🌟 Scraping Stardust Coffee & Video events...")
    
    url = "https://stardustvideoandcoffee.wordpress.com/events-2/"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find the upcoming events widget
        upcoming_events = soup.find('ul', class_='upcoming-events')
        
        if not upcoming_events:
            print("❌ Could not find upcoming events section")
            return []
        
        # Parse each event
        event_items = upcoming_events.find_all('li')
        print(f"📋 Found {len(event_items)} potential events")
        
        for item in event_items:
            try:
                # Extract event title
                title_elem = item.find('strong', class_='event-summary')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract date/time
                when_elem = item.find('span', class_='event-when')
                if not when_elem:
                    continue
                    
                when_text = when_elem.get_text(strip=True)
                
                # Parse the date/time format: "August 21, 2025 at 7:15 pm – 11:15 pm"
                date_match = re.search(r'(\w+ \d+, \d+) at (\d+:\d+ [ap]m)', when_text)
                if not date_match:
                    print(f"⚠️  Could not parse date for: {title}")
                    continue
                
                date_str = date_match.group(1)  # "August 21, 2025"
                time_str = date_match.group(2)  # "7:15 pm"
                
                # Convert to standard format
                try:
                    event_datetime = datetime.strptime(f"{date_str} {time_str}", "%B %d, %Y %I:%M %p")
                    event_date = event_datetime.strftime("%Y-%m-%d")
                    event_time = event_datetime.strftime("%H:%M")
                except ValueError as e:
                    print(f"⚠️  Date parsing error for {title}: {e}")
                    continue
                
                # Create event object
                event = {
                    'title': title,
                    'date': event_date,
                    'time': event_time,
                    'venue': 'Stardust Coffee & Video',
                    'venue_url': 'https://stardustvideoandcoffee.wordpress.com',
                    'url': url,  # Events page URL
                    'description': f"Live music at Stardust Coffee & Video. Phone 407.623.3393 for more info.",
                    'when_text': when_text,
                    'source': 'stardust'
                }
                
                events.append(event)
                print(f"   ✅ {title} - {event_date} at {event_time}")
                
            except Exception as e:
                print(f"   ❌ Error parsing event: {e}")
                continue
        
        print(f"🌟 Successfully scraped {len(events)} Stardust events")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Stardust: {e}")
        return []

def save_events(events, filename='stardust_events.json'):
    """Save events to JSON file"""
    with open(filename, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to {filename}")

if __name__ == "__main__":
    events = scrape_stardust_events()
    if events:
        save_events(events)
        
        print("\n📋 STARDUST EVENTS SUMMARY:")
        print("=" * 30)
        for event in events:
            print(f"🎵 {event['title']}")
            print(f"   📅 {event['date']} at {event['time']}")
            print(f"   📍 {event['venue']}")
            print()
    else:
        print("❌ No events found")
