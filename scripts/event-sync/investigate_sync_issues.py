#!/usr/bin/env python3
"""
Event Sync Issues Investigation Tool
===================================
Comprehensive diagnosis of Conduit missing events and Will's Pub duplicates
"""

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

import requests


class SyncIssuesInvestigator:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

    def get_current_gancio_events(self):
        """Get all current events from Gancio"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                print(f"✅ Retrieved {len(events)} events from Gancio API")
                return events
            else:
                print(f"❌ Failed to get Gancio events: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting Gancio events: {e}")
            return []

    def analyze_gancio_events(self, events):
        """Analyze current Gancio events for patterns and duplicates"""
        print("\n📊 GANCIO EVENTS ANALYSIS")
        print("=" * 30)

        if not events:
            print("❌ No events to analyze")
            return

        # Count by venue/place
        venue_counts = defaultdict(int)
        place_counts = defaultdict(int)
        titles = []

        for event in events:
            title = event.get("title", "Unknown")
            place_id = event.get("place_id", "unknown")
            place_name = (
                event.get("place", {}).get("name", f"Place ID {place_id}")
                if isinstance(event.get("place"), dict)
                else f"Place ID {place_id}"
            )

            titles.append(title)
            venue_counts[place_name] += 1
            place_counts[place_id] += 1

        print("🏢 Events by Venue:")
        for venue, count in venue_counts.items():
            print(f"   • {venue}: {count} events")

        print("\n🔢 Events by Place ID:")
        for place_id, count in place_counts.items():
            print(f"   • Place ID {place_id}: {count} events")

        # Check for duplicates
        title_counts = Counter(titles)
        duplicates = {
            title: count for title, count in title_counts.items() if count > 1
        }

        if duplicates:
            print(f"\n❌ DUPLICATE EVENTS FOUND ({len(duplicates)} titles):")
            for title, count in duplicates.items():
                print(f'   • "{title}" appears {count} times')
        else:
            print("\n✅ No duplicate event titles found")

        # Look for Conduit events
        conduit_events = [e for e in events if "conduit" in str(e).lower()]
        print(f"\n🎯 Conduit Events: {len(conduit_events)} found")

        if conduit_events:
            print("   📋 Conduit events in Gancio:")
            for event in conduit_events[:5]:  # Show first 5
                print(f"   • {event.get('title', 'Unknown')}")
        else:
            print("   ❌ NO Conduit events found in Gancio")

    def get_scraped_events(self):
        """Get events from scrapers to compare with Gancio"""
        print("\n📥 SCRAPER EVENTS ANALYSIS")
        print("=" * 30)

        scraped_events = {"willspub": [], "conduit": []}

        # Import scrapers and get events
        sys.path.insert(0, "scripts/event-sync")

        try:
            print("🎸 Scraping Will's Pub events...")
            from enhanced_multi_venue_sync import scrape_willspub_events

            willspub_events = scrape_willspub_events()
            scraped_events["willspub"] = willspub_events or []
            print(f"   ✅ Found {len(scraped_events['willspub'])} Will's Pub events")
        except Exception as e:
            print(f"   ❌ Will's Pub scraper error: {e}")

        try:
            print("\n🎤 Scraping Conduit events...")
            from conduit_scraper import scrape_conduit_events

            conduit_events = scrape_conduit_events(download_images=False)
            scraped_events["conduit"] = conduit_events or []
            print(f"   ✅ Found {len(scraped_events['conduit'])} Conduit events")
        except Exception as e:
            print(f"   ❌ Conduit scraper error: {e}")

        return scraped_events

    def compare_scraped_vs_gancio(self, scraped_events, gancio_events):
        """Compare scraped events with what's in Gancio"""
        print("\n🔄 SCRAPED vs GANCIO COMPARISON")
        print("=" * 35)

        gancio_titles = {e.get("title", "") for e in gancio_events}

        for venue, events in scraped_events.items():
            print(f"\n🎯 {venue.upper()} Events:")
            print(f"   📊 Scraped: {len(events)}")

            if not events:
                print("   ❌ No events scraped")
                continue

            # Check how many are in Gancio
            scraped_titles = {e.get("title", "") for e in events}
            in_gancio = scraped_titles.intersection(gancio_titles)
            missing_from_gancio = scraped_titles - gancio_titles

            print(f"   ✅ In Gancio: {len(in_gancio)}")
            print(f"   ❌ Missing from Gancio: {len(missing_from_gancio)}")

            if missing_from_gancio:
                print("   📋 Missing events:")
                for title in list(missing_from_gancio)[:5]:  # Show first 5
                    print(f"      • {title}")
                if len(missing_from_gancio) > 5:
                    print(f"      ... and {len(missing_from_gancio) - 5} more")

    def check_authentication(self):
        """Test Gancio authentication"""
        print("\n🔐 AUTHENTICATION TEST")
        print("=" * 25)

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        print(f"   📧 Email: {email}")
        print(f"   🔑 Password: {'✅ Set' if password else '❌ Not set'}")

        if not password:
            print("   ❌ GANCIO_PASSWORD environment variable required")
            return False

        # Test different authentication methods
        auth_methods = [
            (
                "POST /api/auth/login",
                f"{self.gancio_base_url}/api/auth/login",
                {"email": email, "password": password},
            ),
            (
                "POST /auth/login",
                f"{self.gancio_base_url}/auth/login",
                {"email": email, "password": password},
            ),
        ]

        for method_name, url, data in auth_methods:
            try:
                print(f"\n   🧪 Testing {method_name}...")
                response = self.session.post(url, json=data)
                print(f"      Status: {response.status_code}")
                print(f"      Response size: {len(response.text)} chars")

                if "admin" in response.url or response.status_code == 200:
                    print("      ✅ Authentication successful")
                    return True
                else:
                    print("      ❌ Authentication failed")

            except Exception as e:
                print(f"      ❌ Error: {e}")

        return False

    def test_event_submission(self):
        """Test submitting a sample event to Gancio"""
        print("\n🧪 EVENT SUBMISSION TEST")
        print("=" * 28)

        # Create test events for both venues
        test_events = [
            {
                "title": "TEST: Will's Pub Sync Check",
                "venue": "Will's Pub",
                "place_id": 1,
                "description": "Test event to verify Will's Pub sync - please delete",
            },
            {
                "title": "TEST: Conduit Sync Check",
                "venue": "Conduit",
                "place_id": 3,
                "description": "Test event to verify Conduit sync - please delete",
            },
        ]

        for test_event in test_events:
            print(f"\n   🎯 Testing {test_event['venue']} event submission...")

            gancio_data = {
                "title": test_event["title"],
                "description": test_event["description"],
                "start_datetime": int(datetime.now().timestamp()),
                "end_datetime": int(datetime.now().timestamp()) + 7200,
                "place_id": test_event["place_id"],
                "tags": ["test"],
            }

            # Test different API endpoints
            endpoints = [
                f"{self.gancio_base_url}/api/event",
                f"{self.gancio_base_url}/add",
            ]

            for endpoint in endpoints:
                try:
                    response = self.session.post(endpoint, json=gancio_data)
                    print(f"      📡 {endpoint}: HTTP {response.status_code}")

                    if response.status_code == 200:
                        print(f"      ✅ Event created successfully")
                        result = response.json()
                        event_id = result.get("id", "unknown")
                        print(f"      📋 Event ID: {event_id}")
                    else:
                        print(f"      ❌ Failed - Response: {response.text[:200]}")

                except Exception as e:
                    print(f"      ❌ Error: {e}")

    def check_gallery_flyers(self):
        """Check flyers in gallery vs events in Gancio"""
        print("\n🖼️ GALLERY FLYERS ANALYSIS")
        print("=" * 30)

        flyers_dir = "scripts/event-sync/flyers"

        if not os.path.exists(flyers_dir):
            print("❌ Flyers directory not found")
            return

        flyer_files = [
            f for f in os.listdir(flyers_dir) if f.endswith((".jpg", ".jpeg", ".png"))
        ]

        # Count by venue
        willspub_flyers = [f for f in flyer_files if not f.startswith("conduit-")]
        conduit_flyers = [f for f in flyer_files if f.startswith("conduit-")]

        print(f"📊 Total flyers: {len(flyer_files)}")
        print(f"   • Will's Pub flyers: {len(willspub_flyers)}")
        print(f"   • Conduit flyers: {len(conduit_flyers)}")

        # Show recent Conduit flyers
        if conduit_flyers:
            print("\n📋 Recent Conduit flyers (last 5):")
            conduit_flyers.sort(
                key=lambda x: os.path.getmtime(os.path.join(flyers_dir, x)),
                reverse=True,
            )
            for flyer in conduit_flyers[:5]:
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(flyers_dir, flyer))
                )
                print(f"   • {flyer} - {mtime.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("\n❌ No Conduit flyers found in gallery")

    def investigate_all(self):
        """Run complete investigation"""
        print("🔍 EVENT SYNC ISSUES INVESTIGATION")
        print("=" * 40)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get current state
        gancio_events = self.get_current_gancio_events()
        self.analyze_gancio_events(gancio_events)

        # Get scraped events
        scraped_events = self.get_scraped_events()

        # Compare
        self.compare_scraped_vs_gancio(scraped_events, gancio_events)

        # Check authentication
        auth_success = self.check_authentication()

        # Test event submission if authenticated
        if auth_success:
            self.test_event_submission()

        # Check gallery
        self.check_gallery_flyers()

        # Summary
        print("\n📋 INVESTIGATION SUMMARY")
        print("=" * 28)

        print("✅ Completed checks:")
        print("   • Gancio events analysis")
        print("   • Scraper events retrieval")
        print("   • Scraped vs Gancio comparison")
        print("   • Authentication testing")
        print("   • Gallery flyers analysis")

        if auth_success:
            print("   • Event submission testing")

        print("\n💡 Next steps based on findings above:")
        print("   1. Review authentication results")
        print("   2. Check for missing events in each venue")
        print("   3. Investigate duplicate event causes")
        print("   4. Test event submission endpoints")


if __name__ == "__main__":
    investigator = SyncIssuesInvestigator()
    investigator.investigate_all()
