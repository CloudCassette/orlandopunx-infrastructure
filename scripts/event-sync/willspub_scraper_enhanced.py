#!/usr/bin/env python3
"""
🎸 Enhanced Will's Pub Event Scraper with Proper Date/Time Parsing
================================================================
Correctly scrapes events from Will's Pub with accurate dates and times
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import os
from urllib.parse import urljoin, urlparse
import hashlib

def parse_willspub_datetime(date_text, time_text):
    """Parse Will's Pub date and time format"""
    event_date = "2025-08-20"  # default
    event_time = "19:00"       # default
    
    try:
        if date_text:
            # Format: "Aug 21, 2025"
            date_match = re.search(r'(\w{3})\s+(\d{1,2}),\s+(\d{4})', date_text)
            if date_match:
                month_str, day, year = date_match.groups()
                # Convert month abbreviation to number
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                if month_str in month_map:
                    month = month_map[month_str]
                    parsed_date = datetime(int(year), month, int(day))
                    event_date = parsed_date.strftime('%Y-%m-%d')
        
        if time_text:
            # Format: "07:00 PM"
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_text.upper())
            if time_match:
                hour, minute, period = time_match.groups()
                hour = int(hour)
                
                # Convert to 24-hour format
                if period == 'PM' and hour != 12:
                    hour += 12
                elif period == 'AM' and hour == 12:
                    hour = 0
                    
                event_time = f"{hour:02d}:{minute}"
    
    except Exception as e:
        print(f"   ⚠️  Date/time parsing error: {e}")
        pass
    
    return event_date, event_time

def scrape_willspub_events():
    """Scrape events from Will's Pub with correct selectors and enhanced date parsing"""
    print("🎸 Scraping Will's Pub events with ENHANCED logic...")
    
    url = "https://willspub.org"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Look for Will's Pub event links (tm-event pattern)
        event_links = soup.find_all('a', href=re.compile(r'/tm-event/'))
        
        print(f"📋 Found {len(event_links)} Will's Pub event links")
        
        # Remove duplicates by URL
        unique_events = {}
        for link in event_links:
            event_url = urljoin(url, link.get('href'))
            title = link.get_text(strip=True)
            
            # Skip empty titles or very short ones
            if not title or len(title) < 3:
                continue
                
            # Skip obvious navigation/button text
            if title.lower() in ['event', 'events', 'more info', 'details']:
                continue
                
            unique_events[event_url] = title
        
        print(f"📋 Found {len(unique_events)} unique Will's Pub events")
        
        for event_url, title in unique_events.items():
            try:
                print(f"   📝 Processing: {title}")
                
                # Get event details from individual page
                event_response = requests.get(event_url, headers=headers, timeout=30)
                event_response.raise_for_status()
                
                event_soup = BeautifulSoup(event_response.content, 'html.parser')
                
                # Extract date and time from the event page
                date_element = event_soup.find('span', class_='tw-event-date')
                time_element = event_soup.find('span', class_='tw-event-time')
                
                date_text = date_element.get_text(strip=True) if date_element else None
                time_text = time_element.get_text(strip=True) if time_element else None
                
                # Parse date and time
                event_date, event_time = parse_willspub_datetime(date_text, time_text)
                
                event = {
                    'title': title,
                    'date': event_date,
                    'time': event_time,
                    'venue': "Will's Pub",
                    'venue_url': 'https://willspub.org',
                    'url': event_url,
                    'description': f"Live music at Will's Pub",
                    'source': 'willspub',
                    'raw_date': date_text,
                    'raw_time': time_text
                }
                
                events.append(event)
                print(f"   ✅ {title} - {event_date} at {event_time}")
                
            except Exception as e:
                print(f"   ❌ Error processing {title}: {e}")
                continue
        
        print(f"🎸 Successfully scraped {len(events)} Will's Pub events")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []

if __name__ == "__main__":
    events = scrape_willspub_events()
    
    # Save results
    with open('willspub_events_enhanced.json', 'w') as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to willspub_events_enhanced.json")
    
    # Print results with actual dates
    print(f"\n🎯 ENHANCED RESULTS:")
    for event in events[:10]:  # Show first 10
        print(f"• {event['title']} - {event['date']} at {event['time']}")
        if event.get('raw_date'):
            print(f"  Raw: {event['raw_date']} | {event['raw_time']}")
