#!/usr/bin/env python3
"""
Enhanced Will's Pub to Gancio Sync
- Scrapes events and downloads flyers
- Posts summary to Discord for easy review
- Smart duplicate detection
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

import getpass
from datetime import datetime, timedelta

class EnhancedWillsPubSync:
    def __init__(self, discord_webhook_url=None):
        self.willspub_url = "https://willspub.org"
        self.gancio_url = "http://localhost:13120"
        self.discord_webhook = discord_webhook_url
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        
        # Create directories for flyers
        os.makedirs('flyers', exist_ok=True)
        os.makedirs('../../backups/willspub-flyers', exist_ok=True)
        
    def authenticate_gancio(self, gancio_url, email=None, password=None):
        """Authenticate with Gancio using environment variables or parameters"""
        self.gancio_base_url = gancio_url.rstrip('/')
        self.gancio_authenticated = False
        
        # Get credentials from environment or parameters
        gancio_email = email or os.environ.get('GANCIO_EMAIL')
        gancio_password = password or os.environ.get('GANCIO_PASSWORD')
        
        if not gancio_email or not gancio_password:
            print("⚠️  No Gancio credentials provided - skipping website updates")
            return False
        
        try:
            login_data = {
                'email': gancio_email,
                'password': gancio_password
            }
            
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Gancio authentication successful!")
                self.gancio_authenticated = True
                return True
            else:
                print(f"❌ Gancio authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Gancio authentication error: {e}")
            return False

    def add_event_to_gancio(self, event):
        """Add a single event to Gancio"""
        if not hasattr(self, 'gancio_authenticated') or not self.gancio_authenticated:
            return False
            
        try:
            # Convert date string to timestamp
            event_date = event.get('date', '')
            event_time = event.get('time', '19:00')
            
            # Parse the date
            if event_date:
                # Assuming format is YYYY-MM-DD
                date_obj = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                start_timestamp = int(date_obj.timestamp()) * 1000  # Gancio uses milliseconds
                end_timestamp = start_timestamp + (3 * 3600 * 1000)  # 3 hours later
            else:
                print(f"   ❌ No date for event: {event.get('title', 'Unknown')}")
                return False
            
            # Prepare event data for Gancio
            gancio_event = {
                "title": event.get('title', ''),
                "description": event.get('description', ''),
                "start_datetime": start_timestamp,
                "end_datetime": end_timestamp,
                "place_id": 1,  # Will's Pub place ID
                "tags": ["live-music", "willspub"],
                "recurrent": False,
                "online": False
            }
            
            # Add source URL to description
            if event.get('url'):
                gancio_event['description'] += f"\n\nMore info: {event['url']}"
            
            print(f"   📤 Adding to Gancio: {event.get('title', 'Unknown')}")
            
            response = self.session.post(
                f"{self.gancio_base_url}/add",
                data=json.dumps(gancio_event),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Added to Gancio: {event.get('title', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Failed to add to Gancio: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error adding to Gancio: {e}")
            return False

    def authenticate_gancio(self, gancio_url, email=None, password=None):
        """Authenticate with Gancio using environment variables"""
        self.gancio_base_url = gancio_url.rstrip('/')
        self.gancio_authenticated = False
        
        gancio_email = email or os.environ.get('GANCIO_EMAIL')
        gancio_password = password or os.environ.get('GANCIO_PASSWORD')
        
        if not gancio_email or not gancio_password:
            print("⚠️  No Gancio credentials - skipping website integration")
            return False
        
        try:
            login_data = {'email': gancio_email, 'password': gancio_password}
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data)
            
            if response.status_code == 200:
                print("✅ Gancio authentication successful!")
                self.gancio_authenticated = True
                return True
            else:
                print(f"❌ Gancio auth failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Gancio auth error: {e}")
            return False
    
    def add_event_to_gancio(self, event):
        """Add event to Gancio"""
        if not getattr(self, 'gancio_authenticated', False):
            return False
            
        try:
            from datetime import datetime
            
            event_date = event.get('date', '')
            event_time = event.get('time', '19:00')
            
            if event_date:
                date_obj = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                start_timestamp = int(date_obj.timestamp()) * 1000
                end_timestamp = start_timestamp + (3 * 3600 * 1000)
            else:
                return False
            
            gancio_event = {
                "title": event.get('title', ''),
                "description": event.get('description', '') + f"\n\nMore info: {event.get('url', '')}",
                "start_datetime": start_timestamp,
                "end_datetime": end_timestamp,
                "place_id": 1,
                "tags": ["live-music", "willspub"],
                "recurrent": False,
                "online": False
            }
            
            response = self.session.post(
                f"{self.gancio_base_url}/add",
                json=gancio_event,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Added to website: {event.get('title', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Failed to add: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def download_flyer(self, event_url, event_title):
        """Download show flyer from event page"""
        try:
            print(f"🖼️  Downloading flyer for: {event_title}")
            response = self.session.get(event_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for event images - prioritize Open Graph meta tags
            flyer_urls = []
            
            # First, check Open Graph meta tags (most reliable for event flyers)
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                og_url = og_image.get('content')
                # Skip default Will's Pub logo
                if 'wills-pub-logo' not in og_url.lower():
                    flyer_urls.append(og_url)
                    print(f"📸 Found OG image: {og_url}")
            
            # If no OG image or it's the logo, check for other meta images
            if not flyer_urls:
                twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
                if twitter_image and twitter_image.get('content'):
                    twitter_url = twitter_image.get('content')
                    if 'wills-pub-logo' not in twitter_url.lower():
                        flyer_urls.append(twitter_url)
                        print(f"📸 Found Twitter image: {twitter_url}")
            
            # Fallback: Look for large images in the page content
            if not flyer_urls:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    alt = img.get('alt', '').lower()
                    
                    # Skip logos and small images
                    if 'logo' in src.lower() or 'logo' in alt:
                        continue
                        
                    # Look for event flyers (usually larger images)
                    if any(keyword in src.lower() for keyword in ['event', 'show', 'flyer', 'poster']):
                        flyer_urls.append(urljoin(event_url, src))
                    elif any(keyword in alt for keyword in ['flyer', 'poster', 'show']):
                        flyer_urls.append(urljoin(event_url, src))
                    elif img.get('width') and int(img.get('width', 0)) > 400:  # Large images likely flyers
                        flyer_urls.append(urljoin(event_url, src))
                
                if flyer_urls:
                    print(f"📸 Found fallback image: {flyer_urls[0]}")
            
            # Download the first flyer found
            if flyer_urls:
                flyer_url = flyer_urls[0]
                try:
                    img_response = self.session.get(flyer_url, timeout=30)
                    img_response.raise_for_status()
                    
                    # Generate filename
                    file_ext = os.path.splitext(urlparse(flyer_url).path)[1] or '.jpg'
                    safe_title = re.sub(r'[^\w\s-]', '', event_title).strip()[:50]
                    safe_title = re.sub(r'[\s]+', '_', safe_title)
                    filename = f"{safe_title}_{hashlib.md5(flyer_url.encode()).hexdigest()[:8]}{file_ext}"
                    
                    # Save flyer
                    flyer_path = f"flyers/{filename}"
                    with open(flyer_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"✅ Downloaded flyer: {filename}")
                    return flyer_path, flyer_url
                    
                except Exception as e:
                    print(f"⚠️ Failed to download flyer: {e}")
                    return None, flyer_url
            
            return None, None
            
        except Exception as e:
            print(f"⚠️ Error getting flyer for {event_title}: {e}")
            return None, None
    
    def scrape_willspub_events(self, limit=20):
        """Scrape events from Will's Pub website with flyers"""
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
                                        
                                        # Download flyer
                                        flyer_path, flyer_url = self.download_flyer(url, title)
                                        
                                        events.append({
                                            'title': title,
                                            'date': event_date,
                                            'time': '19:00',  # Default time
                                            'venue': "Will's Pub",
                                            'url': url,
                                            'description': f"Live music event at Will's Pub\n\nSource: {url}",
                                            'flyer_path': flyer_path,
                                            'flyer_url': flyer_url
                                        })
                                        
                                        if len(events) >= limit:
                                            break
                            except Exception as e:
                                print(f"⚠️ Error parsing event: {e}")
                                continue
            
            print(f"✅ Found {len(events)} events with flyers")
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
    
    def post_to_discord(self, summary_text, new_events):
        """Post sync summary to Discord"""
        if not self.discord_webhook:
            print("ℹ️ No Discord webhook configured")
            return
            
        try:
            # Prepare Discord message
            embed = {
                "title": "🎸 Will's Pub Event Sync Complete",
                "description": summary_text,
                "color": 5763719,  # Orange color
                "timestamp": datetime.now().isoformat(),
                "fields": []
            }
            
            # Add some featured events
            if new_events:
                featured_events = new_events[:5]  # Show first 5 events
                event_list = "\n".join([
                    f"**{event['title']}**\n📅 {event['date']} at {event['venue']}\n🔗 {event['url']}\n"
                    for event in featured_events
                ])
                
                embed["fields"].append({
                    "name": f"🎯 Featured New Events ({len(featured_events)} of {len(new_events)})",
                    "value": event_list[:1024],  # Discord limit
                    "inline": False
                })
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(self.discord_webhook, json=payload)
            if response.status_code == 204:
                print("✅ Posted summary to Discord")
            else:
                print(f"⚠️ Discord post failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Error posting to Discord: {e}")
    
    def sync_events(self):
        """Main sync function"""
        print("🎸 Starting Enhanced Will's Pub to OrlandoPunx.com sync...")
        
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
        summary_text = f"📊 **Sync Results:**\n• Total events: {len(new_events)}\n• New events: {len(unique_events)}\n• Duplicates filtered: {len(new_events) - len(unique_events)}\n• Flyers downloaded: {len([e for e in new_events if e.get('flyer_path')])}"
        
        with open('sync_summary.txt', 'w') as f:
            f.write(f"Will's Pub Sync Summary - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total events scraped: {len(new_events)}\n")
            f.write(f"New events found: {len(unique_events)}\n")
            f.write(f"Duplicates filtered: {len(new_events) - len(unique_events)}\n")
            f.write(f"Flyers downloaded: {len([e for e in new_events if e.get('flyer_path')])}\n\n")
            
            if unique_events:
                f.write("NEW EVENTS TO REVIEW:\n")
                f.write("-" * 30 + "\n")
                for i, event in enumerate(unique_events, 1):
                    f.write(f"{i}. {event['title']}\n")
                    f.write(f"   Date: {event['date']}\n")
                    f.write(f"   URL: {event['url']}\n")
                    if event.get('flyer_path'):
                        f.write(f"   Flyer: {event['flyer_path']}\n")
                    f.write("\n")
        
        # Post to Discord
        self.post_to_discord(summary_text, unique_events)
        
        return len(unique_events) > 0

if __name__ == "__main__":
    # Get Discord webhook from environment or command line
    discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    
    # Get Gancio configuration
    gancio_url = os.environ.get('GANCIO_URL', 'https://orlandopunx.com')
    gancio_email = os.environ.get('GANCIO_EMAIL')
    gancio_password = os.environ.get('GANCIO_PASSWORD')
    
    syncer = EnhancedWillsPubSync(discord_webhook)
    
    # Authenticate with Gancio if credentials are provided
    if gancio_email and gancio_password:
        print("🌐 Connecting to Gancio...")
        syncer.authenticate_gancio(gancio_url, gancio_email, gancio_password)
    
    
    # Gancio setup
    gancio_url = os.environ.get('GANCIO_URL', 'https://orlandopunx.com')
    if os.environ.get('GANCIO_EMAIL') and os.environ.get('GANCIO_PASSWORD'):
        print("🌐 Setting up Gancio integration...")
        syncer.authenticate_gancio(gancio_url)
    
    has_new_events = syncer.sync_events()
    
    if has_new_events:
        print("🎯 New events found! Check Discord for summary")
        sys.exit(0)
    
        
        # Add new events to Gancio if authenticated
        if hasattr(self, 'gancio_authenticated') and self.gancio_authenticated and unique_events:
            print("🌐 Adding events to orlandopunx.com...")
            gancio_added = 0
            for event in unique_events:
                if self.add_event_to_gancio(event):
                    gancio_added += 1
            
            if gancio_added > 0:
                summary_lines.append(f"🌐 Added {gancio_added} events to orlandopunx.com")
                print(f"✅ Added {gancio_added} events to orlandopunx.com")
            else:
                print("⚠️  No events were added to orlandopunx.com")
        
        else:
        print("ℹ️ No new events found")
        sys.exit(0)
