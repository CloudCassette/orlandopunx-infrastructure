#!/usr/bin/env python3
"""
Comprehensive Event Sync Issues Fix Tool
========================================
Fixes authentication, deduplication, and missing event issues
"""

import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime

import requests


class EventSyncFixer:
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

        # Venue configurations based on investigation
        self.venue_configs = {
            "Will's Pub": {"place_id": 1, "working_auth_method": "form"},
            "Conduit": {"place_id": 3, "working_auth_method": "form"},
        }

    def fix_authentication(self):
        """Fix Gancio authentication using working method from existing scripts"""
        print("🔧 FIXING AUTHENTICATION")
        print("=" * 30)

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        print(f"📧 Using email: {email}")

        # Method 1: Form-based login (like working scripts)
        try:
            print("🧪 Testing form-based authentication...")

            # First, get the login page to establish session and cookies
            login_page_response = self.session.get(f"{self.gancio_base_url}/login")
            print(f"   Login page: HTTP {login_page_response.status_code}")

            # Submit form data (not JSON)
            login_data = {"email": email, "password": password}

            # Post as form data
            auth_response = self.session.post(
                f"{self.gancio_base_url}/auth/login",
                data=login_data,  # Form data, not JSON
                allow_redirects=True,
            )

            print(f"   Auth response: HTTP {auth_response.status_code}")
            print(f"   Final URL: {auth_response.url}")

            # Check if redirected to admin panel (success indicator)
            if "admin" in auth_response.url or auth_response.status_code == 200:
                print("   ✅ Form-based authentication successful!")
                self.authenticated = True
                return True

        except Exception as e:
            print(f"   ❌ Form auth error: {e}")

        # Method 2: Try alternative endpoints
        alternative_endpoints = ["/api/login", "/login", "/admin/login"]

        for endpoint in alternative_endpoints:
            try:
                print(f"🧪 Testing {endpoint}...")
                response = self.session.post(
                    f"{self.gancio_base_url}{endpoint}",
                    data={"email": email, "password": password},
                )
                print(f"   Response: HTTP {response.status_code}")

                if response.status_code == 200 and "admin" in response.url:
                    print("   ✅ Alternative endpoint successful!")
                    self.authenticated = True
                    return True

            except Exception as e:
                print(f"   ❌ {endpoint} error: {e}")

        print("❌ All authentication methods failed")
        return False

    def get_existing_events_with_dedup_info(self):
        """Get existing events with detailed info for deduplication"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                events = response.json()

                # Create deduplication mapping
                dedup_info = {
                    "by_title": defaultdict(list),
                    "by_title_hash": defaultdict(list),
                    "by_venue": defaultdict(list),
                }

                for event in events:
                    title = event.get("title", "").strip()
                    title_hash = hashlib.md5(title.lower().encode()).hexdigest()

                    dedup_info["by_title"][title].append(event)
                    dedup_info["by_title_hash"][title_hash].append(event)

                    # Try to identify venue
                    venue = self.identify_venue_from_event(event)
                    dedup_info["by_venue"][venue].append(event)

                return events, dedup_info
            else:
                print(f"❌ Failed to get events: HTTP {response.status_code}")
                return [], {}
        except Exception as e:
            print(f"❌ Error getting events: {e}")
            return [], {}

    def identify_venue_from_event(self, event):
        """Identify venue from event data"""
        # Check place_id
        place_id = event.get("place_id")
        if place_id == 1:
            return "Will's Pub"
        elif place_id == 3:
            return "Conduit"

        # Check place name
        place = event.get("place", {})
        if isinstance(place, dict):
            place_name = place.get("name", "").lower()
            if "will" in place_name or "pub" in place_name:
                return "Will's Pub"
            elif "conduit" in place_name:
                return "Conduit"

        # Check tags
        tags = event.get("tags", [])
        if any("will" in str(tag).lower() or "pub" in str(tag).lower() for tag in tags):
            return "Will's Pub"
        elif any("conduit" in str(tag).lower() for tag in tags):
            return "Conduit"

        return "Unknown"

    def create_event_with_proper_dedup(self, event_data, existing_dedup_info):
        """Create event with proper deduplication checking"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        title = event_data.get("title", "").strip()
        venue = event_data.get("venue", "Unknown")

        # Check if event already exists
        if title in existing_dedup_info["by_title"]:
            existing_events = existing_dedup_info["by_title"][title]
            print(
                f'   ⚠️  Event "{title}" already exists ({len(existing_events)} times) - skipping'
            )
            return False

        # Create event data for Gancio
        venue_config = self.venue_configs.get(venue, {"place_id": None})
        place_id = venue_config["place_id"]

        if not place_id:
            print(f"   ❌ Unknown venue: {venue}")
            return False

        # Handle different date formats
        try:
            if "date" in event_data and "time" in event_data:
                # Conduit format
                event_datetime = datetime.strptime(
                    f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M"
                )
                start_timestamp = int(event_datetime.timestamp())
            elif "datetime" in event_data:
                # Will's Pub format
                start_timestamp = int(event_data["datetime"].timestamp())
            else:
                print(f"   ❌ Missing datetime info for: {title}")
                return False
        except Exception as e:
            print(f'   ❌ Date parsing error for "{title}": {e}')
            return False

        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours duration

        gancio_event = {
            "title": title,
            "description": event_data.get("description", f"Live music at {venue}"),
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "place_id": place_id,
            "tags": [venue.lower().replace("'", "").replace(" ", "_")],
        }

        # Try multiple API endpoints
        endpoints_to_try = [
            f"{self.gancio_base_url}/api/event",
            f"{self.gancio_base_url}/add",
            f"{self.gancio_base_url}/admin/event",
        ]

        for endpoint in endpoints_to_try:
            try:
                response = self.session.post(endpoint, json=gancio_event, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    event_id = result.get("id", "unknown")
                    print(f'   ✅ "{title}" created (ID: {event_id})')

                    # Update dedup info
                    existing_dedup_info["by_title"][title].append(
                        {"id": event_id, "title": title}
                    )
                    return True
                elif response.status_code == 401:
                    print(f"   ❌ Unauthorized - authentication may have expired")
                    return False
                else:
                    print(f"   ⚠️  {endpoint}: HTTP {response.status_code}")

            except Exception as e:
                print(f"   ❌ {endpoint} error: {e}")

        print(f"   ❌ All endpoints failed for: {title}")
        return False

    def sync_missing_events(self):
        """Sync all missing events with proper deduplication"""
        print("\n🔄 SYNCING MISSING EVENTS")
        print("=" * 30)

        if not self.authenticated:
            print("❌ Not authenticated - cannot sync events")
            return False

        # Get existing events for deduplication
        existing_events, dedup_info = self.get_existing_events_with_dedup_info()
        print(f"📊 Current Gancio events: {len(existing_events)}")

        # Get scraped events
        sys.path.insert(0, "scripts/event-sync")

        total_created = 0
        total_skipped = 0

        # Sync Will's Pub events
        print("\n🎸 Syncing Will's Pub events...")
        try:
            from enhanced_multi_venue_sync import scrape_willspub_events

            willspub_events = scrape_willspub_events()

            if willspub_events:
                print(f"   📋 Found {len(willspub_events)} Will's Pub events to process")

                for event in willspub_events:
                    if self.create_event_with_proper_dedup(event, dedup_info):
                        total_created += 1
                        time.sleep(1)  # Rate limiting
                    else:
                        total_skipped += 1
            else:
                print("   ❌ No Will's Pub events found")

        except Exception as e:
            print(f"   ❌ Will's Pub sync error: {e}")

        # Sync Conduit events
        print(f"\n🎤 Syncing Conduit events...")
        try:
            from conduit_scraper import scrape_conduit_events

            conduit_events = scrape_conduit_events(download_images=False)

            if conduit_events:
                print(f"   📋 Found {len(conduit_events)} Conduit events to process")

                for event in conduit_events:
                    if self.create_event_with_proper_dedup(event, dedup_info):
                        total_created += 1
                        time.sleep(1)  # Rate limiting
                    else:
                        total_skipped += 1
            else:
                print("   ❌ No Conduit events found")

        except Exception as e:
            print(f"   ❌ Conduit sync error: {e}")

        print(f"\n📊 Sync Results:")
        print(f"   ✅ Created: {total_created} events")
        print(f"   ⚠️  Skipped: {total_skipped} events (duplicates or errors)")

        return total_created > 0

    def clean_duplicates(self):
        """Find and report duplicate events (manual cleanup required)"""
        print("\n🧹 DUPLICATE CLEANUP ANALYSIS")
        print("=" * 35)

        existing_events, dedup_info = self.get_existing_events_with_dedup_info()

        duplicates_found = []
        for title, events in dedup_info["by_title"].items():
            if len(events) > 1:
                duplicates_found.append((title, events))

        if duplicates_found:
            print(f"❌ Found {len(duplicates_found)} duplicate event titles:")
            for title, events in duplicates_found:
                print(f'\n   📋 "{title}" ({len(events)} copies):')
                for event in events:
                    event_id = event.get("id", "unknown")
                    venue = self.identify_venue_from_event(event)
                    print(f"      • ID {event_id} - {venue}")

            print(f"\n💡 To clean duplicates:")
            print(f"   1. Visit: {self.gancio_base_url}/admin")
            print(f"   2. Review duplicate events listed above")
            print(f"   3. Delete older or incorrect entries manually")
        else:
            print("✅ No duplicate events found")

    def verify_fix_results(self):
        """Verify that the fixes worked"""
        print("\n✅ VERIFYING FIX RESULTS")
        print("=" * 30)

        # Re-run investigation
        existing_events, dedup_info = self.get_existing_events_with_dedup_info()

        venue_counts = defaultdict(int)
        for venue, events in dedup_info["by_venue"].items():
            venue_counts[venue] = len(events)

        print("📊 Events by venue after fixes:")
        for venue, count in venue_counts.items():
            print(f"   • {venue}: {count} events")

        # Check if we fixed the main issues
        willspub_count = venue_counts.get("Will's Pub", 0)
        conduit_count = venue_counts.get("Conduit", 0)

        print(f"\n🎯 Issue Resolution Check:")
        if conduit_count > 1:  # Was 1 before
            print(f"   ✅ Conduit events: {conduit_count} (was 1) - IMPROVED")
        else:
            print(f"   ❌ Conduit events: {conduit_count} (still low)")

        if willspub_count > 13:  # Was 13 before
            print(f"   ✅ Will's Pub events: {willspub_count} (was 13) - IMPROVED")
        else:
            print(f"   ⚠️  Will's Pub events: {willspub_count} (was 13)")

    def run_complete_fix(self):
        """Run the complete fix process"""
        print("🔧 COMPREHENSIVE EVENT SYNC FIX")
        print("=" * 40)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Step 1: Fix authentication
        if not self.fix_authentication():
            print("\n❌ Cannot proceed without authentication")
            print("💡 Possible solutions:")
            print("   1. Check GANCIO_PASSWORD environment variable")
            print("   2. Verify Gancio admin credentials")
            print("   3. Check if Gancio is running and accessible")
            return False

        # Step 2: Analyze current duplicates
        self.clean_duplicates()

        # Step 3: Sync missing events
        if self.sync_missing_events():
            print("✅ Events synced successfully")
        else:
            print("❌ Event sync had issues")

        # Step 4: Verify results
        self.verify_fix_results()

        print(f"\n🎯 Fix Process Complete!")
        print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n💡 Next Steps:")
        print(f"   1. Check Gancio admin: {self.gancio_base_url}/admin")
        print(f"   2. Review and approve new events")
        print(f"   3. Clean up any remaining duplicates manually")
        print(f"   4. Test the enhanced sync script for future runs")


if __name__ == "__main__":
    fixer = EventSyncFixer()
    fixer.run_complete_fix()
