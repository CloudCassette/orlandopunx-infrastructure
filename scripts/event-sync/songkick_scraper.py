#!/usr/bin/env python3
"""
🎸 Songkick Event Scraper
========================
Scrapes event data for Uncle Lou's from Songkick
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def scrape_songkick_events(venue_url):
    """Scrape events from a Songkick venue page"""
    print(f"🎤 Scraping Songkick: {venue_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(venue_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find event listings
        event_listings = soup.find_all('li', class_='event-listing')
        print(f"📋 Found {len(event_listings)} potential Songkick events")
        
        for listing in event_listings:
            try:
                # Get event title
                title_element = listing.find('strong', class_='artists')
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue
                
                # Get date
                date_element = listing.find('time', class_='date')
                date_str = date_element.get('datetime', '') if date_element else ''
                
                # Get time (Songkick doesn't always have this)
                time = "19:00"  # Default to 7 PM
                
                # Get venue name
                venue_name = "Uncle Lou's"
                
                # Get event URL
                event_url_element = listing.find('a', class_='event-link')
                event_url = f"https://www.songkick.com{event_url_element.get('href')}" if event_url_element else venue_url
                
                event = {
                    'title': title,
                    'date': date_str,
                    'time': time,
                    'venue': venue_name,
                    'venue_url': venue_url,
                    'url': event_url,
                    'description': f"Event at {venue_name}",
                    'source': 'songkick'
                }
                
                events.append(event)
                
            except Exception as e:
                print(f"   ❌ Error processing Songkick event: {e}")
                continue
        
        print(f"✅ Successfully scraped {len(events)} Songkick events")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Songkick: {e}")
        return []

if __name__ == "__main__":
    # Test with Uncle Lou's URLs
    urls_to_scrape = [
        "https://www.songkick.com/venues/103814-uncle-lous",
        "https://www.songkick.com/venues/1265956-uncle-lous-entertainment-hall"
    ]
    
    all_events = []
    for url in urls_to_scrape:
        all_events.extend(scrape_songkick_events(url))
    
    # Remove duplicates by title
    unique_events = {event['title']: event for event in all_events}.values()
    
    # Save to file
    with open('songkick_events.json', 'w') as f:
        json.dump(list(unique_events), f, indent=2)
    
    print(f"\n💾 Saved {len(unique_events)} unique Songkick events to songkick_events.json")
    
    # Print results
    print(f"\n🎯 RESULTS:")
    for event in unique_events:
        print(f"• {event['title']} - {event['date']}")
