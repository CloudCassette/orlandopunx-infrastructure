#!/usr/bin/env python3
"""
🎸 Fixed Will's Pub Event Scraper
=================================
Correctly scrapes events from Will's Pub by targeting tm-event links
"""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def scrape_willspub_events():
    """Scrape events from Will's Pub with correct selectors"""
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

        # Look for Will's Pub event links (tm-event pattern)
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

                # Parse date (format: "Monday August 18, 2025")
                event_date = "2025-08-20"  # default
                event_time = "19:00"  # default

                if date_element:
                    date_text = date_element.get_text(strip=True)
                    # Try to parse various date formats
                    try:
                        # Common format: "Monday August 18, 2025"
                        date_match = re.search(r"(\w+\s+\d{1,2},\s+\d{4})", date_text)
                        if date_match:
                            parsed_date = datetime.strptime(
                                date_match.group(1), "%B %d, %Y"
                            )
                            event_date = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass

                if time_element:
                    time_text = time_element.get_text(strip=True)
                    # Try to extract time (format: "7:00 pm")
                    time_match = re.search(
                        r"(\d{1,2}:\d{2})\s*(am|pm)", time_text.lower()
                    )
                    if time_match:
                        time_str = time_match.group(1)
                        period = time_match.group(2)

                        # Convert to 24-hour format
                        hour, minute = time_str.split(":")
                        hour = int(hour)
                        if period == "pm" and hour != 12:
                            hour += 12
                        elif period == "am" and hour == 12:
                            hour = 0
                        event_time = f"{hour:02d}:{minute}"

                event = {
                    "title": title,
                    "date": event_date,
                    "time": event_time,
                    "venue": "Will's Pub",
                    "venue_url": "https://willspub.org",
                    "url": event_url,
                    "description": f"Live music at Will's Pub",
                    "source": "willspub",
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
    with open("willspub_events_fixed.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to willspub_events_fixed.json")

    # Print results
    print(f"\n🎯 RESULTS:")
    for event in events:
        print(f"• {event['title']} - {event['date']} at {event['time']}")
