#!/usr/bin/env python3
"""
🎸 Sync Any JSON Events to Gancio
=================================
Syncs events from any JSON file to Gancio approval queue
Based on working willspub_to_gancio_final_working.py pattern
"""

import getpass
import json
import os
import sys
from datetime import datetime

import requests


class GenericGancioSync:
    def __init__(self, gancio_url="https://orlandopunx.com"):
        self.gancio_base_url = gancio_url
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        self.authenticated = False

        # Place IDs (from working script)
        self.places = {
            "Will's Pub": 1,
            "Stardust Coffee & Video": 2,
            "Conduit": 3,  # Assuming Conduit gets ID 3
        }

    def authenticate(self):
        """Authenticate with Gancio using environment variables or prompts"""
        print("🔑 Gancio Authentication")

        # Try to get credentials from environment first
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            password = getpass.getpass("Enter your Gancio password: ")
        else:
            print(f"📧 Using email: {email}")
            print("🔑 Using password from environment")

        login_data = {"email": email, "password": password}

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True
            )

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

    def convert_to_timestamp(self, event):
        """Convert event date/time to timestamp"""
        try:
            start_datetime = datetime.strptime(
                f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M"
            )
            return int(start_datetime.timestamp())
        except:
            return None

    def submit_event(self, event):
        """Submit a single event to Gancio"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        start_timestamp = self.convert_to_timestamp(event)
        if not start_timestamp:
            print("   ❌ Invalid date/time")
            return False

        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later

        # Get place ID
        venue_name = event.get("venue", "Conduit")
        place_id = self.places.get(venue_name, 5)  # Default to Conduit ID

        # Build description
        description_parts = []
        if event.get("description"):
            description_parts.append(event["description"])

        if event.get("price"):
            description_parts.append(f"Tickets: {event['price']}")

        if event.get("age_restriction"):
            description_parts.append(f"Age: {event['age_restriction']}")

        if event.get("url"):
            description_parts.append(f"More info: {event['url']}")

        description = " | ".join(description_parts)

        # Create Gancio event format (based on working script)
        gancio_event = {
            "title": event["title"],
            "description": description,
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "tags": (
                ["conduit", "live-music", "orlando"]
                if event["source"] == "conduit"
                else [event["source"], "live-music", "orlando"]
            ),
            "placeId": place_id,
            "multidate": False,
        }

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/add", json=gancio_event, timeout=30
            )

            if response.status_code == 200:
                print(f"   ✅ Event submitted for approval: {event['title']}")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code}: {response.text[:100]}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def sync_events_from_file(self, filename):
        """Load and sync events from JSON file"""
        try:
            with open(filename, "r") as f:
                events = json.load(f)

            print(f"📋 Loaded {len(events)} events from {filename}")

            # Filter to only Conduit events if syncing combined file
            if filename in ["combined_events.json", "combined_events_fixed.json"]:
                conduit_events = [e for e in events if e.get("source") == "conduit"]
                if conduit_events:
                    events = conduit_events
                    print(f"🎸 Filtering to {len(events)} Conduit events")

            if not events:
                print("📭 No events to sync")
                return

            print(f"🔄 Submitting {len(events)} events to Gancio...")

            submitted = 0
            failed = 0

            for event in events:
                if self.submit_event(event):
                    submitted += 1
                else:
                    failed += 1

            print(f"\n📊 SYNC RESULTS:")
            print(f"   ✅ Submitted: {submitted} events")
            print(f"   ❌ Failed: {failed} events")

            if submitted > 0:
                print(f"\n📋 Next steps:")
                print(
                    f"   1. Go to your Gancio admin panel at https://orlandopunx.com/admin"
                )
                print(f"   2. Review and approve the submitted events")
                print(f"   3. They will then appear on https://orlandopunx.com")

        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in: {filename}")


if __name__ == "__main__":
    # Allow specifying JSON file via command line
    filename = "conduit_events.json"  # Default
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print(f"🎵 Syncing events from {filename} to Gancio")
    print("=" * 50)

    syncer = GenericGancioSync()

    if syncer.authenticate():
        syncer.sync_events_from_file(filename)
    else:
        print("❌ Authentication failed. Check your credentials.")
        print("💡 Make sure GANCIO_PASSWORD is set in your environment")
