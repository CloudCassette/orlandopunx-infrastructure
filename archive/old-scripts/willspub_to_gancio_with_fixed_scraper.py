#!/usr/bin/env python3
"""
🎸 Will's Pub to Gancio Sync - Using FIXED Scraper
================================================
Uses the enhanced multi-venue scraper that captures real event titles
"""

import getpass
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Import our fixed scraper functions
from enhanced_multi_venue_sync import scrape_willspub_events


class FixedGancioSync:
    def __init__(self):
        self.gancio_url = "http://localhost:13120"
        self.session = requests.Session()

        # Set headers
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

        self.gancio_authenticated = False

    def authenticate_gancio(self, email=None, password=None):
        """Authenticate with Gancio"""
        print("🔑 Gancio Authentication")

        if not email:
            email = input("Enter your Gancio email: ")
        if not password:
            password = getpass.getpass("Enter your password: ")

        try:
            # Login to Gancio
            login_data = {"email": email, "password": password}

            response = self.session.post(
                f"{self.gancio_url}/api/auth/login", json=login_data
            )

            if response.status_code == 200:
                print("✅ Authentication successful!")
                self.gancio_authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                if response.text:
                    print(f"Error details: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_existing_events(self):
        """Get existing events from Gancio to avoid duplicates"""
        try:
            response = self.session.get(f"{self.gancio_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                return {event["title"]: event for event in events}
            return {}
        except Exception as e:
            print(f"⚠️  Could not fetch existing events: {e}")
            return {}

    def submit_event_to_gancio(self, event):
        """Submit an event to Gancio"""
        if not self.gancio_authenticated:
            print("❌ Not authenticated with Gancio")
            return False

        try:
            # Convert our event format to Gancio format
            start_datetime = f"{event['date']}T{event['time']}:00"
            end_datetime = f"{event['date']}T{event['time']}:00"  # Same for now

            gancio_event = {
                "title": event["title"],
                "description": event.get("description", f"Event at {event['venue']}"),
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "place_name": event["venue"],
                "place_address": (
                    "1042 N. Mills Ave. Orlando, FL 32803"
                    if event["venue"] == "Will's Pub"
                    else ""
                ),
                "tags": (
                    ["punk"]
                    if any(
                        word in event["title"].lower()
                        for word in ["punk", "hardcore", "metal"]
                    )
                    else []
                ),
            }

            response = self.session.post(
                f"{self.gancio_url}/api/events", json=gancio_event
            )

            if response.status_code in [200, 201]:
                print(f"   ✅ Event submitted for approval: {event['title']}")
                return True
            else:
                print(f"   ❌ Failed to submit {event['title']}: {response.status_code}")
                if response.text:
                    print(f"   Error details: {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error submitting {event['title']}: {e}")
            return False


def main():
    """Main sync function using FIXED scraper"""
    print("🎵 Will's Pub to Gancio Sync - USING FIXED SCRAPER")
    print("=" * 60)
    print("Events will be submitted to your approval queue")
    print("=" * 60)

    # Initialize syncer
    syncer = FixedGancioSync()

    # Authenticate
    if not syncer.authenticate_gancio():
        print("❌ Authentication failed. Exiting.")
        return

    # Get existing events to avoid duplicates
    print("📋 Checking for existing events...")
    existing_events = syncer.get_existing_events()
    print(f"Found {len(existing_events)} existing events")

    # Scrape events using our FIXED scraper
    print("📥 Scraping events from Will's Pub using FIXED scraper...")
    events = scrape_willspub_events()

    if not events:
        print("📭 No events found to sync")
        return

    # Filter out events that already exist
    new_events = []
    for event in events:
        if event["title"] not in existing_events:
            new_events.append(event)
        else:
            print(f"   ⏭️  Skipping existing event: {event['title']}")

    if not new_events:
        print("📭 No new events to sync (all events already exist)")
        return

    print(f"✅ Found {len(new_events)} NEW events to sync")

    # Show preview
    print("\n" + "=" * 50)
    print("NEW EVENTS TO BE SUBMITTED:")
    print("=" * 50)

    for i, event in enumerate(new_events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   📅 {event['date']} at {event['time']}")
        print(f"   📍 {event['venue']}")
        print(f"   🔗 {event['url']}")

    # Confirm submission
    print("\n" + "=" * 50)
    confirm = input(
        f"Submit these {len(new_events)} NEW events to your approval queue? (y/N): "
    )

    if confirm.lower() != "y":
        print("❌ Sync cancelled")
        return

    print("\n🚀 Submitting events...")

    submitted = 0
    failed = 0

    for i, event in enumerate(new_events, 1):
        print(f"\n[{i}/{len(new_events)}] {event['title']}")

        if syncer.submit_event_to_gancio(event):
            submitted += 1
        else:
            failed += 1

    print(f"\n✨ Sync Complete!")
    print(f"   ✅ Submitted: {submitted} events")
    print(f"   ❌ Failed: {failed} events")

    if submitted > 0:
        print(f"\n📋 Next steps:")
        print(f"   1. Go to your Gancio admin panel")
        print(f"   2. Review and approve the submitted events")
        print(f"   3. They will then appear on https://orlandopunx.com")


if __name__ == "__main__":
    main()
