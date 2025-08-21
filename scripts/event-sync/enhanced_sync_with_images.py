#!/usr/bin/env python3
"""
🤖 Enhanced Orlando Punk Events Sync - WITH IMAGES
===================================================
Uses the working event creation method, then attempts to add images
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Import our fixed scraper functions
from enhanced_multi_venue_sync import scrape_willspub_events


class EnhancedGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()

        # Set headers exactly like the working script
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
            }
        )

        # Known place IDs from Gancio
        self.places = {
            "Will's Pub": 1,
            "Uncle Lou's": 2,
            "Lil' Indies": 1,  # Assume same as Will's Pub
        }

        self.authenticated = False

    def authenticate(self):
        """Authenticate with Gancio using the WORKING method"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ Missing GANCIO_PASSWORD environment variable")
            return False

        print(f"🔑 Authenticating with Gancio as {email}...")

        try:
            login_data = {"email": email, "password": password}

            # Temporarily remove Content-Type for login
            original_headers = self.session.headers.copy()
            if "Content-Type" in self.session.headers:
                del self.session.headers["Content-Type"]

            response = self.session.post(
                f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True
            )

            # Restore headers
            self.session.headers.update(original_headers)

            if response.status_code == 200:
                print("✅ Authentication successful!")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def convert_to_timestamp(self, event_data):
        """Convert event date/time to timestamp"""
        try:
            date_str = event_data.get("date", "")
            time_str = event_data.get("time", "19:00")

            if not date_str:
                return None

            # Parse the date and time
            event_datetime = datetime.strptime(
                f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
            )
            return int(event_datetime.timestamp())

        except Exception as e:
            print(f"   ❌ Date conversion error: {e}")
            return None

    def create_event_in_gancio(self, event_data):
        """Create event in Gancio using the WORKING method"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        start_timestamp = self.convert_to_timestamp(event_data)
        if not start_timestamp:
            print("   ❌ Invalid date/time")
            return False

        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later

        # Get place ID
        venue_name = event_data.get("venue", "Will's Pub")
        place_id = self.places.get(venue_name, 1)  # Default to Will's Pub

        # Build description
        description_parts = []
        if event_data.get("description"):
            description_parts.append(event_data["description"])
        if event_data.get("price"):
            description_parts.append(f"Price: {event_data['price']}")
        description_parts.append(f"More info: {event_data.get('source_url', '')}")

        # Create event data in Gancio format (EXACTLY like working script)
        gancio_event = {
            "title": event_data.get("title", ""),
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "description": "\n\n".join(description_parts),
            "tags": ["willspub", "live-music", "orlando"],
            "placeId": place_id,
            "multidate": False,
        }

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/add", json=gancio_event, timeout=30
            )

            if response.status_code == 200:
                print(f"   ✅ Event created: {event_data['title']}")

                # Try to add image if available
                flyer_path = event_data.get("flyer_path")
                if flyer_path and os.path.exists(flyer_path):
                    print(f"   🖼️  Attempting to add image...")
                    # For now, just note that we have an image
                    # TODO: Implement image upload after event creation
                    print(
                        f"   ⚠️  Image upload not yet implemented: {os.path.basename(flyer_path)}"
                    )

                return True
            else:
                print(f"   ❌ Failed: {response.status_code}: {response.text[:100]}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def get_current_events(self):
        """Get current events from Gancio"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []


def main():
    print("🤖 AUTOMATED ORLANDO PUNK EVENTS SYNC")
    print("=" * 50)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize sync
    sync = EnhancedGancioSync()

    # Authenticate
    if not sync.authenticate():
        sys.exit(1)

    # Scrape events
    print("📥 Scraping events with FIXED scraper...")
    events = scrape_willspub_events()

    if not events:
        print("❌ No events found from scraper")
        sys.exit(1)

    print(f"📋 Found {len(events)} events from scraper")

    # Get current events to avoid duplicates
    current_events = sync.get_current_events()
    current_titles = [e.get("title", "") for e in current_events]

    print(f"📊 Current Gancio events: {len(current_events)}")

    # Filter out existing events
    new_events = []
    existing_count = 0

    for event in events:
        if event["title"] not in current_titles:
            new_events.append(event)
        else:
            existing_count += 1

    print(f"🆕 New events to sync: {len(new_events)}")
    print(f"♻️  Existing events skipped: {existing_count}")

    if not new_events:
        print("✨ No new events to sync")
        return

    # Submit new events
    print(f"🚀 Submitting {len(new_events)} new events...")
    success_count = 0

    for event in new_events:
        if sync.create_event_in_gancio(event):
            success_count += 1
        time.sleep(1)  # Small delay between requests

    print(f"✨ Sync complete: {success_count}/{len(new_events)} events submitted")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
