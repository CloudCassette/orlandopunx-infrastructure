#!/usr/bin/env python3
"""
🎸 Sync Conduit Events to Gancio (Fixed Version)
================================================
Syncs Conduit FL events to Gancio approval queue using minimal event structure
Based on analysis of working Conduit event in Gancio
"""

import getpass
import json
import os
import sys
from datetime import datetime

import requests


class ConduitGancioSync:
    def __init__(self, gancio_url="https://orlandopunx.com"):
        self.gancio_base_url = gancio_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }
        )
        self.authenticated = False

        # Conduit place ID (confirmed from working event)
        self.conduit_place_id = 3

    def authenticate(self):
        """Authenticate with Gancio using environment variables"""
        print("🔑 Gancio Authentication")

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD not found in environment")
            return False

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
        except Exception as e:
            print(f"   ❌ Date conversion error: {e}")
            return None

    def submit_event(self, event):
        """Submit a single event to Gancio using minimal structure"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        start_timestamp = self.convert_to_timestamp(event)
        if not start_timestamp:
            print(f"   ❌ Invalid date/time for: {event['title']}")
            return False

        # Use 3-hour duration as default
        end_timestamp = start_timestamp + (3 * 3600)

        # Create MINIMAL Gancio event - matching working event structure exactly
        # NO description, NO tags, NO extra fields
        gancio_event = {
            "title": event["title"],
            "multidate": False,
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "placeId": self.conduit_place_id,
        }

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/add", json=gancio_event, timeout=30
            )

            if response.status_code == 200:
                print(f"   ✅ Event submitted: {event['title']}")
                return True
            else:
                print(f"   ❌ Failed ({response.status_code}): {event['title']}")
                print(f"      Response: {response.text[:100]}")
                return False

        except Exception as e:
            print(f"   ❌ Error submitting {event['title']}: {e}")
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
            print("   (Using minimal event structure - title, time, place only)")

            submitted = 0
            failed = 0

            for i, event in enumerate(events, 1):
                print(f"📝 [{i}/{len(events)}] Processing: {event['title']}")
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
                    f"   1. Go to your Gancio admin panel: https://orlandopunx.com/admin"
                )
                print(f"   2. Click on EVENTS tab (shows {submitted} pending events)")
                print(f"   3. Review and CONFIRM each event to make it public")
                print(f"   4. Events will then appear on https://orlandopunx.com")
                print(
                    f"   \n   💡 NOTE: Events may show 'Will's Pub' in admin due to display bug,"
                )
                print(
                    f"       but they are correctly assigned to Conduit (place ID {self.conduit_place_id})"
                )

        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in: {filename}")


if __name__ == "__main__":
    # Allow specifying JSON file via command line
    filename = "conduit_events.json"  # Default
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print(f"🎵 Syncing Conduit events from {filename} to Gancio")
    print("=" * 55)

    syncer = ConduitGancioSync()

    if syncer.authenticate():
        syncer.sync_events_from_file(filename)
    else:
        print("❌ Authentication failed. Check your credentials.")
        print("💡 Make sure GANCIO_PASSWORD is set in your environment")
