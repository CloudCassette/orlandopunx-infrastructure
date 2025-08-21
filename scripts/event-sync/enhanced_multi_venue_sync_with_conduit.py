#!/usr/bin/env python3
"""
Enhanced Multi-Venue Sync - Includes Conduit Support
===================================================
"""

import json
import os
import sys
from datetime import datetime

import requests
from conduit_scraper import scrape_conduit_events
from enhanced_multi_venue_sync import scrape_willspub_events


class EnhancedGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }
        )
        self.authenticated = False

        # Venue place IDs
        self.venue_place_ids = {
            "Will's Pub": 1,
            "Conduit": 3,  # Based on your existing working script
        }

    def authenticate(self):
        """Authenticate with Gancio"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable not set")
            return False

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/api/auth/login",
                json={"email": email, "password": password},
            )

            if response.status_code == 200:
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def create_event_in_gancio(self, event_data):
        """Create an event in Gancio from venue event data"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        try:
            # Parse date/time
            if "date" in event_data and "time" in event_data:
                event_datetime = datetime.strptime(
                    f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M"
                )
                start_timestamp = int(event_datetime.timestamp())
            else:
                print(f"   ❌ Missing date/time data")
                return False

            end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later

            # Get place ID based on venue
            venue = event_data.get("venue", "Unknown")
            place_id = self.venue_place_ids.get(venue)

            if not place_id:
                print(f"   ❌ Unknown venue: {venue}")
                return False

            gancio_data = {
                "title": event_data["title"],
                "description": event_data.get("description", ""),
                "start_datetime": start_timestamp,
                "end_datetime": end_timestamp,
                "multidate": False,
                "placeId": place_id,
                "tags": [venue.lower().replace("'", "")],
            }

            response = self.session.post(
                f"{self.gancio_base_url}/add", json=gancio_data
            )

            if response.status_code == 200:
                result = response.json()
                print(
                    f"   ✅ {event_data['title']} (Event ID: {result.get('id', 'unknown')})"
                )
                return True
            else:
                print(f"   ❌ Failed to create event: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ Error creating event: {e}")
            return False


def main():
    """Main sync function with multi-venue support"""
    print("🤖 ENHANCED MULTI-VENUE SYNC")
    print("=" * 40)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    syncer = EnhancedGancioSync()

    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1

    # Get existing events to avoid duplicates
    try:
        response = syncer.session.get(f"{syncer.gancio_base_url}/api/events")
        if response.status_code == 200:
            existing_events = {event["title"] for event in response.json()}
            print(f"📊 Current Gancio events: {len(existing_events)}")
        else:
            existing_events = set()
    except:
        existing_events = set()

    total_submitted = 0

    # Scrape Will's Pub events
    print("\n📥 Scraping Will's Pub events...")
    willspub_events = scrape_willspub_events()
    if willspub_events:
        new_willspub = [e for e in willspub_events if e["title"] not in existing_events]
        print(f"🆕 New Will's Pub events: {len(new_willspub)}")

        for event in new_willspub:
            if syncer.create_event_in_gancio(event):
                total_submitted += 1

    # Scrape Conduit events
    print("\n📥 Scraping Conduit events...")
    conduit_events = scrape_conduit_events(download_images=True)
    if conduit_events:
        new_conduit = [e for e in conduit_events if e["title"] not in existing_events]
        print(f"🆕 New Conduit events: {len(new_conduit)}")

        for event in new_conduit:
            if syncer.create_event_in_gancio(event):
                total_submitted += 1

    print(f"\n✨ Sync complete: {total_submitted} events submitted")
    return 0


if __name__ == "__main__":
    exit(main())
