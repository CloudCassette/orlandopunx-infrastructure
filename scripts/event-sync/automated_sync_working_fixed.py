#!/usr/bin/env python3
"""
🤖 Automated Orlando Punk Events Sync - Enhanced Multi-Venue Version
===================================================================
Supports both Will's Pub and Conduit venues with proper authentication
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from conduit_scraper import scrape_conduit_events

# Import both venue scrapers
from enhanced_multi_venue_sync import scrape_willspub_events


class EnhancedGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()

        # Set headers like the working script
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        self.authenticated = False

        # Define venue place IDs (based on your existing working scripts)
        self.venue_place_ids = {"Will's Pub": 1, "Conduit": 3}

    def authenticate(self):
        """Authenticate with Gancio using working method"""
        print("🔑 Authenticating with Gancio...")

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        # Use the working authentication endpoint
        login_url = f"{self.gancio_base_url}/auth/login"
        login_data = {"email": email, "password": password}

        try:
            # First get the login page to establish session
            self.session.get(f"{self.gancio_base_url}/login")

            # Then POST login credentials
            response = self.session.post(
                login_url, data=login_data, allow_redirects=True
            )

            # Check if we're redirected to admin or dashboard (indicates success)
            if "admin" in response.url or response.status_code == 200:
                print("✅ Authentication successful")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def create_event_in_gancio(self, event_data):
        """Create an event in Gancio from scraped event data"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        try:
            # Parse datetime from scraped data
            if "date" in event_data and "time" in event_data:
                # Conduit format: date='2025-08-20', time='21:00'
                event_datetime = datetime.strptime(
                    f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M"
                )
                start_timestamp = int(event_datetime.timestamp())
            elif "datetime" in event_data:
                # Will's Pub format: datetime already parsed
                start_timestamp = int(event_data["datetime"].timestamp())
            else:
                print(f"   ❌ Missing date/time information")
                return False

            end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later

            # Determine venue and place_id
            venue = event_data.get("venue", "Unknown")
            place_id = self.venue_place_ids.get(venue)

            if not place_id:
                print(f"   ❌ Unknown venue: {venue}")
                return False

            # Prepare Gancio event data
            gancio_data = {
                "title": event_data["title"],
                "description": event_data.get("description", ""),
                "start_datetime": start_timestamp,
                "end_datetime": end_timestamp,
                "place_id": place_id,
                "tags": [venue.lower().replace("'", "").replace(" ", "_")],
            }

            # Use the working event creation endpoint
            response = self.session.post(
                f"{self.gancio_base_url}/api/event", json=gancio_data
            )

            if response.status_code == 200:
                result = response.json()
                event_id = result.get("id", "unknown")
                print(f"   ✅ {event_data['title'][:50]}... (ID: {event_id})")
                return True
            else:
                print(f"   ❌ Error: HTTP {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


def main():
    """Main automated sync function with multi-venue support"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("🤖 ENHANCED MULTI-VENUE ORLANDO PUNK EVENTS SYNC")
    print("=" * 55)
    print(f"⏰ Started: {timestamp}")
    print("🎯 Venues: Will's Pub + Conduit")

    # Initialize syncer
    syncer = EnhancedGancioSync()

    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1

    # Get existing events to avoid duplicates
    print("📊 Checking existing events...")
    try:
        response = syncer.session.get(f"{syncer.gancio_base_url}/api/events")
        if response.status_code == 200:
            existing_events = {event["title"] for event in response.json()}
            print(f"📋 Current Gancio events: {len(existing_events)}")
        else:
            existing_events = set()
            print("⚠️  Could not fetch existing events")
    except:
        existing_events = set()
        print("⚠️  Could not fetch existing events")

    total_events = []
    submitted = 0

    # Scrape Will's Pub events
    print("\n📥 Scraping Will's Pub events...")
    try:
        willspub_events = scrape_willspub_events()
        if willspub_events:
            print(f"📋 Found {len(willspub_events)} Will's Pub events")
            total_events.extend(willspub_events)
        else:
            print("📭 No Will's Pub events found")
    except Exception as e:
        print(f"❌ Will's Pub scraping error: {e}")

    # Scrape Conduit events
    print("\n📥 Scraping Conduit events...")
    try:
        conduit_events = scrape_conduit_events(download_images=True)
        if conduit_events:
            print(f"📋 Found {len(conduit_events)} Conduit events")
            total_events.extend(conduit_events)
        else:
            print("📭 No Conduit events found")
    except Exception as e:
        print(f"❌ Conduit scraping error: {e}")

    if not total_events:
        print("📭 No events found from any venue")
        return 0

    print(f"\n📊 Total events from all venues: {len(total_events)}")

    # Filter for new events only
    new_events = [
        event for event in total_events if event["title"] not in existing_events
    ]

    print(f"🆕 New events to sync: {len(new_events)}")
    print(f"♻️  Existing events skipped: {len(total_events) - len(new_events)}")

    if not new_events:
        print("✨ All events already exist - no work to do!")
        return 0

    # Group events by venue for better reporting
    willspub_new = [e for e in new_events if e.get("venue") == "Will's Pub"]
    conduit_new = [e for e in new_events if e.get("venue") == "Conduit"]

    print(f"\n🎯 Venue breakdown:")
    print(f"   • Will's Pub: {len(willspub_new)} new events")
    print(f"   • Conduit: {len(conduit_new)} new events")

    # Submit new events
    print(f"\n🚀 Submitting {len(new_events)} new events...")

    for event in new_events:
        if syncer.create_event_in_gancio(event):
            submitted += 1
        time.sleep(1)  # Be nice to the server

    print(f"\n✨ Sync complete: {submitted}/{len(new_events)} events submitted")

    # Log summary
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ Completed: {end_time}")

    # Summary by venue
    willspub_submitted = sum(
        1 for e in new_events[:submitted] if e.get("venue") == "Will's Pub"
    )
    conduit_submitted = sum(
        1 for e in new_events[:submitted] if e.get("venue") == "Conduit"
    )

    print(f"\n📊 Results by venue:")
    print(f"   • Will's Pub: {willspub_submitted} events added")
    print(f"   • Conduit: {conduit_submitted} events added")

    if submitted > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Check Gancio admin: http://localhost:13120/admin")
        print(f"   2. Review and approve new events")
        print(f"   3. Events will appear on https://orlandopunx.com after approval")

    return 0


if __name__ == "__main__":
    exit(main())
