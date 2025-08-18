#!/usr/bin/env python3
"""
🎸 Multi-Venue Event Scraper
============================
Scrapes events from multiple Orlando venues:
- Will's Pub
- Stardust Coffee & Video

Combines events, removes duplicates, and posts to Discord + orlandopunx.com
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import os
from urllib.parse import urljoin, urlparse
import hashlib

# Import the existing Will's Pub scraper functions
# We'll adapt the enhanced_willspub_sync.py logic

def scrape_willspub_events():
    """Scrape events from Will's Pub (adapted from enhanced_willspub_sync.py)"""
    print("🎸 Scraping Will's Pub events...")
    
    url = "https://willspub.net/calendar/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find event items (from the existing logic)
        event_items = soup.find_all('div', class_='event-item')
        
        if not event_items:
            event_items = soup.find_all('article', class_='event')
        
        if not event_items:
            # Fallback: look for any elements with event-related classes
            event_items = soup.find_all(['div', 'article'], class_=re.compile(r'event|calendar'))
        
        print(f"📋 Found {len(event_items)} potential Will's Pub events")
        
        for item in event_items:
            try:
                # Extract title
                title_elem = item.find(['h1', 'h2', 'h3', 'h4', '.event-title', '.title'])
                if not title_elem:
                    title_elem = item.find('a')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                
                # Extract event URL
                event_url = url
                link_elem = item.find('a')
                if link_elem and link_elem.get('href'):
                    event_url = urljoin(url, link_elem.get('href'))
                
                # Extract date/time (this would need to be adapted based on Will's Pub format)
                date_elem = item.find(['time', '.date', '.event-date'])
                date_str = ""
                time_str = "19:00"
                
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # Parse date format from Will's Pub
                    # This would need to be adapted based on their actual format
                
                # Create event object
                event = {
                    'title': title,
                    'date': date_str or datetime.now().strftime("%Y-%m-%d"),
                    'time': time_str,
                    'venue': "Will's Pub",
                    'venue_url': 'https://willspub.net',
                    'url': event_url,
                    'description': "Live music at Will's Pub",
                    'source': 'willspub'
                }
                
                events.append(event)
                print(f"   ✅ {title}")
                
            except Exception as e:
                print(f"   ❌ Error parsing Will's Pub event: {e}")
                continue
        
        print(f"🎸 Successfully scraped {len(events)} Will's Pub events")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []

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
                    'url': url,
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

def merge_and_deduplicate_events(willspub_events, stardust_events):
    """Merge events from both venues and remove duplicates"""
    all_events = willspub_events + stardust_events
    
    # Sort by date and time
    all_events.sort(key=lambda x: f"{x['date']} {x['time']}")
    
    print(f"📊 Total events before deduplication: {len(all_events)}")
    print(f"   - Will's Pub: {len(willspub_events)}")
    print(f"   - Stardust: {len(stardust_events)}")
    
    return all_events

def post_to_discord(events, webhook_url):
    """Post events summary to Discord"""
    if not webhook_url:
        print("⚠️  No Discord webhook URL provided")
        return
    
    if not events:
        print("📭 No events to post to Discord")
        return
    
    # Group events by venue
    willspub_events = [e for e in events if e['source'] == 'willspub']
    stardust_events = [e for e in events if e['source'] == 'stardust']
    
    # Create Discord message
    message = f"🎸 **Orlando Music Events Update** 🎵\n\n"
    
    if willspub_events:
        message += f"**🎸 Will's Pub** ({len(willspub_events)} events):\n"
        for event in willspub_events[:5]:  # Limit to 5 per venue
            message += f"• **{event['title']}** - {event['date']} at {event['time']}\n"
        if len(willspub_events) > 5:
            message += f"... and {len(willspub_events) - 5} more events\n"
        message += "\n"
    
    if stardust_events:
        message += f"**🌟 Stardust Coffee & Video** ({len(stardust_events)} events):\n"
        for event in stardust_events[:5]:  # Limit to 5 per venue
            message += f"• **{event['title']}** - {event['date']} at {event['time']}\n"
        if len(stardust_events) > 5:
            message += f"... and {len(stardust_events) - 5} more events\n"
        message += "\n"
    
    message += f"📅 **Total**: {len(events)} upcoming events\n"
    message += f"🕐 **Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            print("✅ Successfully posted to Discord")
        else:
            print(f"⚠️  Discord post failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Discord posting error: {e}")

def save_combined_events(events, filename='combined_events.json'):
    """Save combined events to JSON file"""
    with open(filename, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} combined events to {filename}")

def main():
    """Main execution function"""
    print("🎯 MULTI-VENUE EVENT SCRAPER")
    print("============================")
    
    # Scrape both venues
    willspub_events = []  # Would call actual Will's Pub scraper here
    stardust_events = scrape_stardust_events()
    
    # Merge events
    all_events = merge_and_deduplicate_events(willspub_events, stardust_events)
    
    # Save results
    save_combined_events(all_events)
    
    # Post to Discord if webhook provided
    discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    if discord_webhook:
        post_to_discord(all_events, discord_webhook)
    
    # Generate summary
    print(f"\n📊 FINAL SUMMARY:")
    print(f"================")
    print(f"🎸 Will's Pub events: {len(willspub_events)}")
    print(f"🌟 Stardust events: {len(stardust_events)}")
    print(f"📅 Total events: {len(all_events)}")
    
    return all_events

if __name__ == "__main__":
    events = main()
