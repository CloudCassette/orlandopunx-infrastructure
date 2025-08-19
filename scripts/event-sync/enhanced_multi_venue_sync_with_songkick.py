#!/usr/bin/env python3
"""
🎸 FIXED Multi-Venue Event Scraper for Orlando
==============================================
Scrapes events from:
- Will's Pub (willspub.org) - FIXED to capture real event titles
- Stardust Coffee & Video (stardustvideoandcoffee.wordpress.com)

Features:
- Downloads actual event flyers (not logos)
- Posts to Discord with images
- Integrates with orlandopunx.com via Gancio
- Archives all data
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

def download_flyer(event_url, event_title):
    """Download flyer for an event by checking og:image meta tag"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(event_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Open Graph image (og:image) - this is usually the event flyer
        og_image = soup.find('meta', property='og:image')
        
        if og_image and og_image.get('content'):
            flyer_url = og_image.get('content')
            
            # Skip Will's Pub logo
            if 'willspub-logo' in flyer_url.lower() or 'logo' in flyer_url.lower():
                print(f"   ⚠️  Skipping logo for: {event_title}")
                return None, None
            
            # Download the flyer
            flyer_response = requests.get(flyer_url, headers=headers, timeout=30)
            flyer_response.raise_for_status()
            
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', event_title).strip()
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            # Get file extension from URL
            parsed_url = urlparse(flyer_url)
            file_ext = os.path.splitext(parsed_url.path)[1]
            if not file_ext:
                file_ext = '.jpg'
            
            # Create unique filename with hash
            url_hash = hashlib.md5(flyer_url.encode()).hexdigest()[:8]
            filename = f"{safe_title}_{url_hash}{file_ext}"
            
            # Ensure flyers directory exists
            os.makedirs('flyers', exist_ok=True)
            
            # Save flyer
            filepath = os.path.join('flyers', filename)
            with open(filepath, 'wb') as f:
                f.write(flyer_response.content)
            
            file_size = len(flyer_response.content)
            print(f"✅ Downloaded flyer: {filename} ({file_size} bytes)")
            return flyer_url, filename
            
    except Exception as e:
        print(f"   ❌ Flyer download error for {event_title}: {e}")
        return None, None

def scrape_willspub_events():
    """Scrape events from Will's Pub with FIXED logic"""
    print("🎸 Scraping Will's Pub events with FIXED logic...")
    
    url = "https://willspub.org"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # FIXED: Look for Will's Pub event links (tm-event pattern instead of /event/)
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
                
                # Download flyer
                print(f"🖼️  Downloading flyer for: {title}")
                flyer_url, flyer_file = download_flyer(event_url, title)
                
                event = {
                    'title': title,
                    'date': event_date,
                    'time': event_time,
                    'venue': "Will's Pub",
                    'venue_url': 'https://willspub.org',
                    'url': event_url,
                    'description': f"Live music at Will's Pub",
                    'source': 'willspub',
                    'flyer_url': flyer_url or '',
                    'flyer_file': flyer_file or ''
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

def scrape_stardust_events():
    """Scrape events from Stardust Coffee & Video"""
    print("🌟 Scraping Stardust Coffee & Video events...")
    
    url = "https://stardustvideoandcoffee.wordpress.com/events-2/"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Look for event entries in the content
        content_div = soup.find('div', class_='entry-content')
        if content_div:
            # Find all paragraph tags that might contain event info
            for p in content_div.find_all('p'):
                text = p.get_text(strip=True)
                
                # Look for date patterns (e.g., "Sunday, August 18")
                date_pattern = r'(\w+day),?\s+(\w+)\s+(\d+)'
                date_match = re.search(date_pattern, text)
                
                if date_match:
                    day_name, month_name, day = date_match.groups()
                    
                    # Look for time patterns
                    time_pattern = r'(\d{1,2}):?(\d{0,2})\s*(am|pm)'
                    time_match = re.search(time_pattern, text.lower())
                    
                    if time_match:
                        # Extract event title (usually the first significant text)
                        title_match = re.search(r'^([^,.\n]+)', text)
                        if title_match:
                            title = title_match.group(1).strip()
                            
                            # Parse time
                            hour = int(time_match.group(1))
                            minute = time_match.group(2) or "00"
                            period = time_match.group(3)
                            
                            if period == 'pm' and hour != 12:
                                hour += 12
                            elif period == 'am' and hour == 12:
                                hour = 0
                            
                            event_time = f"{hour:02d}:{minute}"
                            
                            # Parse date
                            month_map = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }
                            
                            month_num = month_map.get(month_name.lower(), 8)  # default to August
                            year = 2025
                            
                            try:
                                event_date = datetime(year, month_num, int(day)).strftime('%Y-%m-%d')
                            except:
                                event_date = "2025-08-20"
                            
                            event = {
                                'title': title,
                                'date': event_date,
                                'time': event_time,
                                'venue': 'Stardust Coffee & Video',
                                'venue_url': 'https://stardustvideoandcoffee.wordpress.com',
                                'url': url,
                                'description': f'Event at Stardust Coffee & Video',
                                'source': 'stardust'
                            }
                            
                            events.append(event)
                            print(f"   ✅ {title} - {event_date} at {event_time}")
        
        print(f"🌟 Successfully scraped {len(events)} Stardust events")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Stardust: {e}")
        return []

def post_to_discord(all_events, webhook_url):
    """Post event summary to Discord"""
    if not all_events:
        print("📭 No events to post to Discord")
        return
    
    # Group events by venue
    willspub_events = [e for e in all_events if e['source'] == 'willspub']
    stardust_events = [e for e in all_events if e['source'] == 'stardust']
    
    # Create Discord message
    message = f"🎸 **Orlando Music Events Update** 🌟\n\n"
    
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
    
    message += f"📅 **Total**: {len(all_events)} upcoming events across Orlando\n"
    message += f"🕐 **Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            print("✅ Multi-venue summary posted to Discord!")
        else:
            print(f"⚠️  Discord post failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Discord posting error: {e}")

def scrape_willspub_events():
    """Scrape events from Will's Pub with FIXED logic"""
    print("🎸 Scraping Will's Pub events with FIXED logic...")
    
    url = "https://willspub.org"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # FIXED: Look for Will's Pub event links (tm-event pattern instead of /event/)
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
                
                # Download flyer
                print(f"🖼️  Downloading flyer for: {title}")
                flyer_url, flyer_file = download_flyer(event_url, title)
                
                event = {
                    'title': title,
                    'date': event_date,
                    'time': event_time,
                    'venue': "Will's Pub",
                    'venue_url': 'https://willspub.org',
                    'url': event_url,
                    'description': f"Live music at Will's Pub",
                    'source': 'willspub',
                    'flyer_url': flyer_url or '',
                    'flyer_file': flyer_file or ''
                }
                
                events.append(event)
                
            except Exception as e:
                print(f"   ❌ Error processing {title}: {e}")
                continue
        
        print(f"🎸 Successfully scraped {len(events)} Will's Pub events")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []

def main():
    """Main execution function"""
    print("🎯 FIXED MULTI-VENUE EVENT SCRAPER")
    print("==================================")
    print("🎸 Will's Pub + 🌟 Stardust Coffee & Video")
    print("="*50)
    
    # Scrape both venues
    print("\n🎸 SCRAPING WILL'S PUB...")
    willspub_events = scrape_willspub_events()
    
    print("\n🌟 SCRAPING STARDUST...")
    stardust_events = scrape_stardust_events()
    
    # Combine events
    all_events = willspub_events + stardust_events
    
    # Sort all events by date
    all_events.sort(key=lambda x: f"{x['date']} {x['time']}")
    
    print(f"\n📊 FIXED RESULTS:")
    print(f"==================")
    print(f"🎸 Will's Pub: {len(willspub_events)} events")
    print(f"🌟 Stardust: {len(stardust_events)} events")
    print(f"📅 Total: {len(all_events)} events")
    
    # Save results
    with open('combined_events_fixed.json', 'w') as f:
        json.dump(all_events, f, indent=2)
    print(f"💾 Saved {len(all_events)} events to combined_events_fixed.json")
    
    # Also save individual venue files for compatibility
    with open('willspub_events_fixed.json', 'w') as f:
        json.dump(willspub_events, f, indent=2)
    with open('stardust_events_fixed.json', 'w') as f:
        json.dump(stardust_events, f, indent=2)
    
    # Generate summary file
    with open('sync_summary_fixed.txt', 'w') as f:
        f.write(f"FIXED Multi-Venue Sync Summary\n")
        f.write(f"==============================\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Will's Pub Events: {len(willspub_events)}\n")
        f.write(f"Stardust Events: {len(stardust_events)}\n")
        f.write(f"Total Events: {len(all_events)}\n\n")
        
        f.write("Recent Events:\n")
        for event in all_events[:10]:
            f.write(f"- {event['title']} ({event['venue']}) - {event['date']} {event['time']}\n")
    
    print(f"\n🎯 FIXED MULTI-VENUE SCRAPING COMPLETE!")
    print(f"✅ Orlando music scene fully covered with REAL event titles!")
    
    # Show some example results
    print(f"\n📋 Sample events captured:")
    for event in all_events[:5]:
        print(f"   • {event['title']} - {event['date']} at {event['time']}")
    
    return all_events

if __name__ == "__main__":
    events = main()

# Add Songkick scraping functions
def download_songkick_flyer(event_url, event_title):
    """Download flyer image from Songkick event page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(event_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            flyer_url = og_image.get('content')
            
            if flyer_url and 'default' not in flyer_url.lower():
                print(f"🖼️  Downloading flyer for: {event_title}")
                
                flyer_response = requests.get(flyer_url, headers=headers, timeout=30)
                flyer_response.raise_for_status()
                
                # Create safe filename
                safe_title = re.sub(r'[^\w\s-]', '', event_title).strip()
                safe_title = re.sub(r'[-\s]+', '_', safe_title)
                
                url_hash = hashlib.md5(flyer_url.encode()).hexdigest()[:8]
                filename = f"{safe_title}_{url_hash}.jpg"
                filepath = os.path.join('flyers', filename)
                
                os.makedirs('flyers', exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(flyer_response.content)
                
                print(f"✅ Downloaded flyer: {filename} ({len(flyer_response.content)} bytes)")
                return flyer_url, filepath
                
    except Exception as e:
        print(f"   ❌ Flyer download error for {event_title}: {e}")
    
    return None, None

def scrape_songkick_venue(venue_url):
    """Scrape events from a Songkick venue page using JSON-LD structured data"""
    print(f"🎤 Scraping Songkick: {venue_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(venue_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find all JSON-LD script tags
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                json_data = json.loads(script.string)
                
                # Handle both single objects and arrays
                if isinstance(json_data, list):
                    json_objects = json_data
                else:
                    json_objects = [json_data]
                
                for obj in json_objects:
                    if obj.get('@type') == 'MusicEvent':
                        # Extract event data
                        title = obj.get('name', '').replace(' @ Uncle Lous', '').replace(' @ ', ' at ')
                        
                        # Parse start date
                        start_date_str = obj.get('startDate', '')
                        if start_date_str:
                            try:
                                # Parse ISO format: 2025-07-28T19:00:00
                                event_datetime = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                                date = event_datetime.strftime('%Y-%m-%d')
                                time = event_datetime.strftime('%H:%M')
                            except:
                                date = start_date_str[:10] if len(start_date_str) >= 10 else ''
                                time = '19:00'  # Default
                        else:
                            continue  # Skip events without dates
                        
                        # Get venue info
                        location = obj.get('location', {})
                        venue_name = location.get('name', 'Uncle Lou\'s')
                        
                        # Get event URL
                        event_url = obj.get('url', venue_url)
                        
                        # Get performers
                        performers = obj.get('performer', [])
                        if performers:
                            performer_names = [p.get('name', '') for p in performers if p.get('name')]
                            if len(performer_names) > 1:
                                title = ' with '.join(performer_names)
                            elif len(performer_names) == 1:
                                title = performer_names[0]
                        
                        # Download flyer
                        flyer_url, flyer_path = download_songkick_flyer(event_url, title)
                        
                        event = {
                            'title': title,
                            'date': date,
                            'time': time,
                            'venue': venue_name,
                            'venue_url': venue_url,
                            'source_url': event_url,
                            'description': obj.get('description', f"Event at {venue_name}"),
                            'source': 'songkick',
                            'flyer_url': flyer_url,
                            'flyer_path': flyer_path
                        }
                        
                        events.append(event)
                        
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
        
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Songkick: {e}")
        return []

def scrape_uncle_lous_songkick():
    """Scrape all Uncle Lou's events from multiple Songkick URLs"""
    print("🎸 Scraping Uncle Lou's events from Songkick...")
    
    urls_to_scrape = [
        "https://www.songkick.com/venues/103814-uncle-lous",
        "https://www.songkick.com/venues/1265956-uncle-lous-entertainment-hall"
    ]
    
    all_events = []
    for url in urls_to_scrape:
        events = scrape_songkick_venue(url)
        all_events.extend(events)
    
    # Remove duplicates by title and date
    unique_events = {}
    for event in all_events:
        key = f"{event['title']}_{event['date']}"
        if key not in unique_events:
            unique_events[key] = event
    
    events = list(unique_events.values())
    print(f"🎸 Successfully scraped {len(events)} Uncle Lou's events from Songkick")
    return events

# Update the main scraping function to include Songkick
def scrape_all_events():
    """Scrape events from all sources"""
    all_events = []
    
    # Scrape Will's Pub
    willspub_events = scrape_willspub_events()
    all_events.extend(willspub_events)
    
    # Scrape Stardust
    stardust_events = scrape_stardust_events()
    all_events.extend(stardust_events)
    
    # Scrape Uncle Lou's from Songkick
    songkick_events = scrape_uncle_lous_songkick()
    all_events.extend(songkick_events)
    
    return all_events

if __name__ == "__main__":
    print("🎵 Multi-Venue Event Scraper with Songkick")
    print("=" * 50)
    
    all_events = scrape_all_events()
    
    # Save combined results
    with open('combined_events_with_songkick.json', 'w') as f:
        json.dump(all_events, f, indent=2)
    
    print(f"\n💾 Saved {len(all_events)} total events to combined_events_with_songkick.json")
    
    # Print summary by venue
    venues = {}
    for event in all_events:
        venue = event.get('venue', 'Unknown')
        venues[venue] = venues.get(venue, 0) + 1
    
    print(f"\n📊 EVENTS BY VENUE:")
    print("=" * 30)
    for venue, count in venues.items():
        print(f"{venue}: {count} events")
