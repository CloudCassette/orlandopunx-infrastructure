#!/usr/bin/env python3
"""
Enhanced Will's Pub to Gancio Sync
- Scrapes events and downloads flyers
- Posts summary to Discord for easy review
- Smart duplicate detection
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class EnhancedWillsPubSync:
    def __init__(self, discord_webhook_url=None):
        self.willspub_url = "https://willspub.org"
        self.gancio_url = "http://localhost:13120"
        self.discord_webhook = discord_webhook_url
        self.session = requests.Session()

        # Set headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
            }
        )

        # Create directories for flyers
        os.makedirs("flyers", exist_ok=True)
        os.makedirs("../../backups/willspub-flyers", exist_ok=True)

    def download_flyer(self, event_url, event_title):
        """Download show flyer from event page"""
        try:
            print(f"🖼️  Downloading flyer for: {event_title}")
            response = self.session.get(event_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for event images
            flyer_urls = []

            # Check for featured images
            for img in soup.find_all("img"):
                src = img.get("src", "")
                alt = img.get("alt", "").lower()

                # Look for event flyers (usually larger images)
                if any(
                    keyword in src.lower()
                    for keyword in ["event", "show", "flyer", "poster"]
                ):
                    flyer_urls.append(urljoin(event_url, src))
                elif any(keyword in alt for keyword in ["flyer", "poster", "show"]):
                    flyer_urls.append(urljoin(event_url, src))
                elif (
                    img.get("width") and int(img.get("width", 0)) > 400
                ):  # Large images likely flyers
                    flyer_urls.append(urljoin(event_url, src))

            # If no specific flyers found, get the first large image
            if not flyer_urls:
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if src and not src.startswith("data:"):
                        flyer_urls.append(urljoin(event_url, src))
                        break

            # Download the first flyer found
            if flyer_urls:
                flyer_url = flyer_urls[0]
                try:
                    img_response = self.session.get(flyer_url, timeout=30)
                    img_response.raise_for_status()

                    # Generate filename
                    file_ext = os.path.splitext(urlparse(flyer_url).path)[1] or ".jpg"
                    safe_title = re.sub(r"[^\w\s-]", "", event_title).strip()[:50]
                    safe_title = re.sub(r"[\s]+", "_", safe_title)
                    filename = f"{safe_title}_{hashlib.md5(flyer_url.encode()).hexdigest()[:8]}{file_ext}"

                    # Save flyer
                    flyer_path = f"flyers/{filename}"
                    with open(flyer_path, "wb") as f:
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

            soup = BeautifulSoup(response.content, "html.parser")
            events = []

            # Look for event scripts or data
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "EventData" in script.string:
                    # Extract event data from JavaScript
                    lines = script.string.split("\n")
                    for line in lines:
                        if (
                            "EventData.events.push" in line
                            and '"type" : "event"' in line
                        ):
                            # Parse event data from the line
                            try:
                                value_match = re.search(r'"value" : "([^"]+)"', line)
                                display_match = re.search(
                                    r'"display" : "([^"]+)"', line
                                )
                                url_match = re.search(r'"url" : "([^"]+)"', line)

                                if all([value_match, display_match, url_match]):
                                    display = (
                                        display_match.group(1)
                                        .replace("&amp;", "&")
                                        .replace("&#039;", "'")
                                    )
                                    url = url_match.group(1)

                                    # Parse date from display
                                    date_match = re.search(r"(\d{2}/\d{2})$", display)
                                    if date_match:
                                        title = display[:-6].strip()
                                        date_str = date_match.group(1)

                                        # Convert MM/DD to full date
                                        month, day = date_str.split("/")
                                        current_year = datetime.now().year
                                        event_date = (
                                            f"2025-{month.zfill(2)}-{day.zfill(2)}"
                                        )

                                        # Download flyer
                                        flyer_path, flyer_url = self.download_flyer(
                                            url, title
                                        )

                                        events.append(
                                            {
                                                "title": title,
                                                "date": event_date,
                                                "time": "19:00",  # Default time
                                                "venue": "Will's Pub",
                                                "url": url,
                                                "description": f"Live music event at Will's Pub\n\nSource: {url}",
                                                "flyer_path": flyer_path,
                                                "flyer_url": flyer_url,
                                            }
                                        )

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
                "fields": [],
            }

            # Add some featured events
            if new_events:
                featured_events = new_events[:5]  # Show first 5 events
                event_list = "\n".join(
                    [
                        f"**{event['title']}**\n📅 {event['date']} at {event['venue']}\n🔗 {event['url']}\n"
                        for event in featured_events
                    ]
                )

                embed["fields"].append(
                    {
                        "name": f"🎯 Featured New Events ({len(featured_events)} of {len(new_events)})",
                        "value": event_list[:1024],  # Discord limit
                        "inline": False,
                    }
                )

            payload = {"embeds": [embed]}

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
        existing_titles = {event.get("title", "").lower() for event in existing_events}

        # Filter out duplicates
        unique_events = []
        for event in new_events:
            if event["title"].lower() not in existing_titles:
                unique_events.append(event)

        print(
            f"📊 Found {len(unique_events)} new events (filtered {len(new_events) - len(unique_events)} duplicates)"
        )

        # Save results
        with open("willspub_events.json", "w") as f:
            json.dump(new_events, f, indent=2)

        with open("willspub_new_events.json", "w") as f:
            json.dump(unique_events, f, indent=2)

        # Generate summary
        summary_text = f"📊 **Sync Results:**\n• Total events: {len(new_events)}\n• New events: {len(unique_events)}\n• Duplicates filtered: {len(new_events) - len(unique_events)}\n• Flyers downloaded: {len([e for e in new_events if e.get('flyer_path')])}"

        with open("sync_summary.txt", "w") as f:
            f.write(f"Will's Pub Sync Summary - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total events scraped: {len(new_events)}\n")
            f.write(f"New events found: {len(unique_events)}\n")
            f.write(f"Duplicates filtered: {len(new_events) - len(unique_events)}\n")
            f.write(
                f"Flyers downloaded: {len([e for e in new_events if e.get('flyer_path')])}\n\n"
            )

            if unique_events:
                f.write("NEW EVENTS TO REVIEW:\n")
                f.write("-" * 30 + "\n")
                for i, event in enumerate(unique_events, 1):
                    f.write(f"{i}. {event['title']}\n")
                    f.write(f"   Date: {event['date']}\n")
                    f.write(f"   URL: {event['url']}\n")
                    if event.get("flyer_path"):
                        f.write(f"   Flyer: {event['flyer_path']}\n")
                    f.write("\n")

        # Post to Discord
        self.post_to_discord(summary_text, unique_events)

        return len(unique_events) > 0


if __name__ == "__main__":
    # Get Discord webhook from environment or command line
    discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL")

    syncer = EnhancedWillsPubSync(discord_webhook)
    has_new_events = syncer.sync_events()

    if has_new_events:
        print("🎯 New events found! Check Discord for summary")
        sys.exit(0)
    else:
        print("ℹ️ No new events found")
        sys.exit(0)


def scrape_stardust_events():
    """Scrape events from Stardust Coffee & Video"""
    print("🌟 Scraping Stardust Coffee & Video events...")

    url = "https://stardustvideoandcoffee.wordpress.com/events-2/"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        events = []

        # Find the upcoming events widget
        upcoming_events = soup.find("ul", class_="upcoming-events")

        if not upcoming_events:
            print("❌ Could not find upcoming events section")
            return []

        # Parse each event
        event_items = upcoming_events.find_all("li")
        print(f"📋 Found {len(event_items)} potential events")

        for item in event_items:
            try:
                # Extract event title
                title_elem = item.find("strong", class_="event-summary")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Extract date/time
                when_elem = item.find("span", class_="event-when")
                if not when_elem:
                    continue

                when_text = when_elem.get_text(strip=True)

                # Parse the date/time format: "August 21, 2025 at 7:15 pm – 11:15 pm"
                date_match = re.search(r"(\w+ \d+, \d+) at (\d+:\d+ [ap]m)", when_text)
                if not date_match:
                    print(f"⚠️  Could not parse date for: {title}")
                    continue

                date_str = date_match.group(1)  # "August 21, 2025"
                time_str = date_match.group(2)  # "7:15 pm"

                # Convert to standard format
                try:
                    event_datetime = datetime.strptime(
                        f"{date_str} {time_str}", "%B %d, %Y %I:%M %p"
                    )
                    event_date = event_datetime.strftime("%Y-%m-%d")
                    event_time = event_datetime.strftime("%H:%M")
                except ValueError as e:
                    print(f"⚠️  Date parsing error for {title}: {e}")
                    continue

                # Create event object
                event = {
                    "title": title,
                    "date": event_date,
                    "time": event_time,
                    "venue": "Stardust Coffee & Video",
                    "venue_url": "https://stardustvideoandcoffee.wordpress.com",
                    "url": url,
                    "description": f"Live music at Stardust Coffee & Video. Phone 407.623.3393 for more info.",
                    "when_text": when_text,
                    "source": "stardust",
                    "flyer_url": "",  # Stardust doesn't seem to have flyers
                    "flyer_file": "",
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


# Modify the main execution to include both venues
print("\n" + "=" * 50)
print("🎯 MULTI-VENUE EVENT SCRAPER")
print("🎸 Will's Pub + 🌟 Stardust Coffee & Video")
print("=" * 50)

# Scrape Stardust events
stardust_events = scrape_stardust_events()

# Combine with existing Will's Pub events
if "events" in locals():
    all_events = events + stardust_events
else:
    all_events = stardust_events

# Sort all events by date
all_events.sort(key=lambda x: f"{x['date']} {x['time']}")

print(f"\n📊 COMBINED RESULTS:")
print(f"===================")
willspub_count = len([e for e in all_events if e["source"] == "willspub"])
stardust_count = len([e for e in all_events if e["source"] == "stardust"])
print(f"🎸 Will's Pub: {willspub_count} events")
print(f"🌟 Stardust: {stardust_count} events")
print(f"📅 Total: {len(all_events)} events")

# Save combined events
with open("combined_events.json", "w") as f:
    json.dump(all_events, f, indent=2)

# Update Discord message to include both venues
discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
if discord_webhook_url and all_events:
    print(f"\n💬 Posting combined events to Discord...")

    # Create enhanced message with both venues
    message = f"🎸 **Orlando Music Events Update** 🌟\n\n"

    if willspub_count > 0:
        message += f"**🎸 Will's Pub** ({willspub_count} events):\n"
        willspub_events_list = [e for e in all_events if e["source"] == "willspub"]
        for event in willspub_events_list[:5]:
            message += f"• **{event['title']}** - {event['date']} at {event['time']}\n"
        if len(willspub_events_list) > 5:
            message += f"... and {len(willspub_events_list) - 5} more\n"
        message += "\n"

    if stardust_count > 0:
        message += f"**🌟 Stardust Coffee & Video** ({stardust_count} events):\n"
        stardust_events_list = [e for e in all_events if e["source"] == "stardust"]
        for event in stardust_events_list[:5]:
            message += f"• **{event['title']}** - {event['date']} at {event['time']}\n"
        if len(stardust_events_list) > 5:
            message += f"... and {len(stardust_events_list) - 5} more\n"
        message += "\n"

    message += f"📅 **Total**: {len(all_events)} upcoming events across Orlando\n"
    message += f"🕐 **Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    try:
        payload = {"content": message}
        response = requests.post(discord_webhook_url, json=payload)

        if response.status_code == 204:
            print("✅ Multi-venue summary posted to Discord!")
        else:
            print(f"⚠️  Discord post failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Discord error: {e}")

print(f"\n🎯 MULTI-VENUE SCRAPING COMPLETE!")
print(f"✅ Will's Pub + Stardust integration ready")
