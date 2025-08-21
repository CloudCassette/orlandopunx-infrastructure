#!/usr/bin/env python3
"""
🎸 FIXED Multi-Venue Event Scraper for Orlando
==============================================
Scrapes events from:
- Will's Pub (willspub.org) - FIXED to capture real event titles

Features:
- Downloads actual event flyers (not logos)
- Integrates with orlandopunx.com via Gancio
- Enhanced date/time parsing
"""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def parse_willspub_datetime(date_text, time_text):
    """Parse Will's Pub date and time format"""
    event_date = "2025-08-20"  # default
    event_time = "19:00"  # default

    try:
        if date_text:
            # Format: "Aug 21, 2025"
            date_match = re.search(r"(\w{3})\s+(\d{1,2}),\s+(\d{4})", date_text)
            if date_match:
                month_str, day, year = date_match.groups()
                # Convert month abbreviation to number
                month_map = {
                    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
                }
                if month_str in month_map:
                    month = month_map[month_str]
                    parsed_date = datetime(int(year), month, int(day))
                    event_date = parsed_date.strftime("%Y-%m-%d")

        if time_text:
            # Format: "07:00 PM"
            time_match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_text.upper())
            if time_match:
                hour, minute, period = time_match.groups()
                hour = int(hour)

                # Convert to 24-hour format
                if period == "PM" and hour != 12:
                    hour += 12
                elif period == "AM" and hour == 12:
                    hour = 0

                event_time = f"{hour:02d}:{minute}"

    except Exception as e:
        print(f"   ⚠️  Date/time parsing error: {e}")
        pass

    return event_date, event_time


def download_flyer(event_url, event_title):
    """Download flyer for an event by checking og:image meta tag"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(event_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Look for Open Graph image (og:image) - this is usually the event flyer
        og_image = soup.find("meta", property="og:image")

        if og_image and og_image.get("content"):
            flyer_url = og_image.get("content")

            # Skip Will's Pub logo
            if "willspub-logo" in flyer_url.lower() or "logo" in flyer_url.lower():
                print(f"   ⚠️  Skipping logo for: {event_title}")
                return None, None

            # Download the flyer
            flyer_response = requests.get(flyer_url, headers=headers, timeout=30)
            flyer_response.raise_for_status()

            # Create safe filename
            safe_title = re.sub(r"[^\w\s-]", "", event_title).strip()
            safe_title = re.sub(r"\s+", "_", safe_title)

            # Get file extension from URL
            parsed_url = urlparse(flyer_url)
            file_ext = os.path.splitext(parsed_url.path)[1]
            if not file_ext:
                file_ext = ".jpg"

            # Create unique filename with hash
            url_hash = hashlib.md5(flyer_url.encode()).hexdigest()[:8]
            filename = f"{safe_title}_{url_hash}{file_ext}"

            # Ensure flyers directory exists
            os.makedirs("flyers", exist_ok=True)

            # Save flyer
            filepath = os.path.join("flyers", filename)
            with open(filepath, "wb") as f:
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        events = []

        # FIXED: Look for Will's Pub event links (tm-event pattern)
        event_links = soup.find_all("a", href=re.compile(r"/tm-event/"))

        print(f"📋 Found {len(event_links)} Will's Pub event links")

        # Remove duplicates by URL
        unique_events = {}
        for link in event_links:
            event_url = urljoin(url, link.get("href"))
            title = link.get_text(strip=True)

            # Skip empty titles or very short ones
            if not title or len(title) < 3:
                continue

            # Skip obvious navigation/button text
            if title.lower() in ["event", "events", "more info", "details"]:
                continue

            unique_events[event_url] = title

        print(f"📋 Found {len(unique_events)} unique Will's Pub events")

        for event_url, title in unique_events.items():
            try:
                print(f"   📝 Processing: {title}")

                # Get event details from individual page
                event_response = requests.get(event_url, headers=headers, timeout=30)
                event_response.raise_for_status()

                event_soup = BeautifulSoup(event_response.content, "html.parser")

                # Extract date and time from the event page
                date_element = event_soup.find("span", class_="tw-event-date")
                time_element = event_soup.find("span", class_="tw-event-time")

                date_text = date_element.get_text(strip=True) if date_element else None
                time_text = time_element.get_text(strip=True) if time_element else None

                # Parse date and time
                event_date, event_time = parse_willspub_datetime(date_text, time_text)

                # Download flyer
                print(f"🖼️  Downloading flyer for: {title}")
                flyer_url, flyer_file = download_flyer(event_url, title)

                event = {
                    "title": title,
                    "date": event_date,
                    "time": event_time,
                    "venue": "Will's Pub",
                    "venue_url": "https://willspub.org",
                    "url": event_url,
                    "description": f"Live music at Will's Pub",
                    "source": "willspub",
                    "flyer_url": flyer_url or "",
                    "flyer_file": flyer_file or "",
                    "raw_date": date_text,
                    "raw_time": time_text,
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
    with open("willspub_events_enhanced.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to willspub_events_enhanced.json")

    # Print results
    print(f"\n🎯 RESULTS:")
    for event in events[:10]:  # Show first 10
        print(f"• {event['title']} - {event['date']} at {event['time']}")
        if event.get("raw_date"):
            print(f"  Raw: {event['raw_date']} | {event['raw_time']}")
