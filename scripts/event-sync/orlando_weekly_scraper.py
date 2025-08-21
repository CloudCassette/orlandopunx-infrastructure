#!/usr/bin/env python3
"""
🎸 Orlando Weekly Music Events Scraper
======================================
Scrapes music events from Orlando Weekly's event calendar
Filters to known venues: Will's Pub, Conduit, Uncle Lou's, Stardust, Sly Fox
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def scrape_orlando_weekly_events(download_images=False):
    """Scrape music events from Orlando Weekly"""
    print("🎸 Scraping Orlando Weekly music events...")

    # Target URL for music events
    base_url = "https://www.orlandoweekly.com"
    search_url = f"{base_url}/orlando/EventSearch?eventCategory=2282432&sortType=date&v=d"
    
    # Known venues we want to capture
    target_venues = {
        "Will's Pub": "Will's Pub",
        "Conduit": "Conduit", 
        "Uncle Lou's": "Uncle Lou's",
        "Stardust Video & Coffee": "Stardust Video & Coffee",
        "Stardust Coffee": "Stardust Video & Coffee",  # Alternate name
        "Sly Fox": "Sly Fox"
    }
    
    # Use multiple user agents to avoid blocking
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": user_agents[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print(f"🔍 Fetching: {search_url}")
        response = session.get(search_url, timeout=30)
        response.raise_for_status()
        
        # Check if we hit Cloudflare protection
        if "Attention Required" in response.text or "cf-browser-verification" in response.text:
            print("❌ Hit Cloudflare protection - trying alternative approach...")
            
            # Try with different headers and delay
            time.sleep(2)
            headers["User-Agent"] = user_agents[1]
            session.headers.update(headers)
            
            response = session.get(search_url, timeout=30)
            response.raise_for_status()
            
            if "Attention Required" in response.text:
                print("❌ Still blocked by Cloudflare - manual verification needed")
                return []
        
        soup = BeautifulSoup(response.content, "html.parser")
        events = []
        
        # Look for event listings - Orlando Weekly typically uses specific classes
        event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|listing|item'))
        
        if not event_containers:
            # Fallback: look for links containing event info
            event_containers = soup.find_all('a', href=re.compile(r'/event/|/Event/'))
        
        print(f"📋 Found {len(event_containers)} potential event containers")
        
        for container in event_containers:
            try:
                # Extract event title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                
                # Skip if title contains unwanted content
                if any(skip in title.lower() for skip in ['advertisement', 'sponsored', 'classifieds']):
                    continue
                
                # Look for venue information
                venue_text = ""
                venue_elem = container.find(text=re.compile(r'(Will\'s Pub|Conduit|Uncle Lou\'s|Stardust|Sly Fox)', re.I))
                if venue_elem:
                    venue_text = venue_elem.strip()
                else:
                    # Try to find venue in surrounding text
                    all_text = container.get_text()
                    for venue_name in target_venues.keys():
                        if venue_name.lower() in all_text.lower():
                            venue_text = venue_name
                            break
                
                # Skip if no target venue found
                if not venue_text:
                    continue
                
                # Map to standardized venue name
                mapped_venue = None
                for venue_key, venue_value in target_venues.items():
                    if venue_key.lower() in venue_text.lower():
                        mapped_venue = venue_value
                        break
                
                if not mapped_venue:
                    continue
                
                # Try to extract date information
                date_text = ""
                date_elem = container.find(text=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+day,|\w+ \d{1,2}'))
                if date_elem:
                    date_text = date_elem.strip()
                
                # Parse date (simplified - can be enhanced)
                event_date = "2025-08-21"  # default
                try:
                    if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', date_text):
                        # Handle MM/DD/YYYY or MM-DD-YYYY format
                        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_text)
                        if date_match:
                            month, day, year = date_match.groups()
                            if len(year) == 2:
                                year = f"20{year}"
                            event_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
                
                # Try to extract time
                time_text = ""
                time_elem = container.find(text=re.compile(r'\d{1,2}:\d{2}|\d{1,2}\s*(am|pm)', re.I))
                if time_elem:
                    time_text = time_elem.strip()
                
                event_time = "19:00"  # default 7pm
                try:
                    time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm)', time_text.lower())
                    if time_match:
                        hour, minute, period = time_match.groups()
                        hour = int(hour)
                        minute = int(minute) if minute else 0
                        
                        if period == "pm" and hour != 12:
                            hour += 12
                        elif period == "am" and hour == 12:
                            hour = 0
                        
                        event_time = f"{hour:02d}:{minute:02d}"
                except:
                    pass
                
                # Get event URL
                event_url = base_url
                link_elem = container.find('a')
                if link_elem and link_elem.get('href'):
                    event_url = urljoin(base_url, link_elem.get('href'))
                
                # Create event object
                event = {
                    "title": title,
                    "date": event_date,
                    "time": event_time,
                    "venue": mapped_venue,
                    "venue_url": "",  # Would need individual venue URLs
                    "url": event_url,
                    "description": f"Event at {mapped_venue} via Orlando Weekly",
                    "source": "orlando_weekly",
                    "raw_date": date_text,
                    "raw_time": time_text,
                    "raw_venue": venue_text
                }
                
                events.append(event)
                print(f"   ✅ {title} - {mapped_venue} - {event_date} at {event_time}")
                
            except Exception as e:
                print(f"   ❌ Error processing event: {e}")
                continue
        
        print(f"🎸 Successfully scraped {len(events)} Orlando Weekly events from target venues")
        return events
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error scraping Orlando Weekly: {e}")
        return []
    except Exception as e:
        print(f"❌ Error scraping Orlando Weekly: {e}")
        return []


def test_scraper():
    """Test the Orlando Weekly scraper"""
    print("🧪 Testing Orlando Weekly scraper...")
    events = scrape_orlando_weekly_events()
    
    if events:
        print(f"\n✅ Found {len(events)} events from target venues:")
        venue_counts = {}
        for event in events:
            venue = event['venue']
            venue_counts[venue] = venue_counts.get(venue, 0) + 1
        
        for venue, count in venue_counts.items():
            print(f"   🎸 {venue}: {count} events")
        
        print(f"\n📋 Sample events:")
        for event in events[:3]:
            print(f"   • {event['title']} ({event['venue']}) - {event['date']} at {event['time']}")
    else:
        print("❌ No events found - may need to adjust scraper or handle Cloudflare")


if __name__ == "__main__":
    test_scraper()
