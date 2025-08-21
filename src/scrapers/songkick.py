#!/usr/bin/env python3
"""
🎸 Songkick Event Scraper - FIXED VERSION
==========================================
Extracts structured JSON-LD data from Songkick venue pages
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


def download_songkick_flyer(event_url, event_title):
    """Download flyer image from Songkick event page"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(event_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Look for Open Graph image
        og_image = soup.find("meta", property="og:image")
        if og_image:
            flyer_url = og_image.get("content")

            if flyer_url and "default" not in flyer_url.lower():
                print(f"🖼️  Downloading flyer for: {event_title}")

                flyer_response = requests.get(flyer_url, headers=headers, timeout=30)
                flyer_response.raise_for_status()

                # Create safe filename
                safe_title = re.sub(r"[^\w\s-]", "", event_title).strip()
                safe_title = re.sub(r"[-\s]+", "_", safe_title)

                url_hash = hashlib.md5(flyer_url.encode()).hexdigest()[:8]
                filename = f"{safe_title}_{url_hash}.jpg"
                filepath = os.path.join("flyers", filename)

                os.makedirs("flyers", exist_ok=True)

                with open(filepath, "wb") as f:
                    f.write(flyer_response.content)

                print(
                    f"✅ Downloaded flyer: {filename} ({len(flyer_response.content)} bytes)"
                )
                return flyer_url, filepath

    except Exception as e:
        print(f"   ❌ Flyer download error for {event_title}: {e}")

    return None, None


def scrape_songkick_venue(venue_url):
    """Scrape events from a Songkick venue page using JSON-LD structured data"""
    print(f"🎤 Scraping Songkick: {venue_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(venue_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        events = []

        # Find all JSON-LD script tags
        json_scripts = soup.find_all("script", type="application/ld+json")
        print(f"📋 Found {len(json_scripts)} JSON-LD scripts")

        for script in json_scripts:
            try:
                json_data = json.loads(script.string)

                # Handle both single objects and arrays
                if isinstance(json_data, list):
                    json_objects = json_data
                else:
                    json_objects = [json_data]

                for obj in json_objects:
                    if obj.get("@type") == "MusicEvent":
                        # Extract event data
                        title = (
                            obj.get("name", "")
                            .replace(" @ Uncle Lous", "")
                            .replace(" @ ", " at ")
                        )

                        # Parse start date
                        start_date_str = obj.get("startDate", "")
                        if start_date_str:
                            try:
                                # Parse ISO format: 2025-07-28T19:00:00
                                event_datetime = datetime.fromisoformat(
                                    start_date_str.replace("Z", "+00:00")
                                )
                                date = event_datetime.strftime("%Y-%m-%d")
                                time = event_datetime.strftime("%H:%M")
                            except:
                                date = (
                                    start_date_str[:10]
                                    if len(start_date_str) >= 10
                                    else ""
                                )
                                time = "19:00"  # Default
                        else:
                            continue  # Skip events without dates

                        # Get venue info
                        location = obj.get("location", {})
                        venue_name = location.get("name", "Uncle Lou's")

                        # Get event URL
                        event_url = obj.get("url", venue_url)

                        # Get performers
                        performers = obj.get("performer", [])
                        if performers:
                            performer_names = [
                                p.get("name", "") for p in performers if p.get("name")
                            ]
                            if len(performer_names) > 1:
                                title = " with ".join(performer_names)
                            elif len(performer_names) == 1:
                                title = performer_names[0]

                        # Download flyer
                        flyer_url, flyer_path = download_songkick_flyer(
                            event_url, title
                        )

                        event = {
                            "title": title,
                            "date": date,
                            "time": time,
                            "venue": venue_name,
                            "venue_url": venue_url,
                            "source_url": event_url,
                            "description": obj.get(
                                "description", f"Event at {venue_name}"
                            ),
                            "source": "songkick",
                            "flyer_url": flyer_url,
                            "flyer_path": flyer_path,
                        }

                        events.append(event)
                        print(f"✅ Found event: {title} - {date} at {time}")

            except json.JSONDecodeError as e:
                print(f"   ❌ JSON decode error: {e}")
                continue
            except Exception as e:
                print(f"   ❌ Error processing JSON-LD: {e}")
                continue

        print(f"🎯 Successfully scraped {len(events)} Songkick events")
        return events

    except Exception as e:
        print(f"❌ Error scraping Songkick: {e}")
        return []


def scrape_uncle_lous_songkick():
    """Scrape all Uncle Lou's events from multiple Songkick URLs"""
    urls_to_scrape = [
        "https://www.songkick.com/venues/103814-uncle-lous",
        "https://www.songkick.com/venues/1265956-uncle-lous-entertainment-hall",
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

    return list(unique_events.values())


if __name__ == "__main__":
    print("🎸 Songkick Uncle Lou's Event Scraper")
    print("=" * 50)

    events = scrape_uncle_lous_songkick()

    # Save to file
    with open("songkick_events_fixed.json", "w") as f:
        json.dump(events, f, indent=2)

    print(
        f"\n💾 Saved {len(events)} unique Songkick events to songkick_events_fixed.json"
    )

    # Print results
    print(f"\n🎯 UNCLE LOU'S EVENTS FROM SONGKICK:")
    print("=" * 50)
    for event in events:
        print(f"• {event['title']}")
        print(f"  📅 {event['date']} at {event['time']}")
        print(f"  📍 {event['venue']}")
        if event.get("flyer_path"):
            print(f"  🖼️  Flyer: {event['flyer_path']}")
        print()
