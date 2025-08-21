#!/usr/bin/env python3
"""
Enhanced Sync Script with Complete Validation
- Robust deduplication using multiple matching strategies
- Venue validation with fallbacks
- Comprehensive error handling and logging
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import requests

# Add path for importing scrapers
sys.path.append("/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync")


class RobustDeduplicator:
    def __init__(self, existing_events: List[Dict]):
        self.existing_events = existing_events
        self.indexed_events = {}
        self.content_hashes = {}
        self._index_events()

    def _index_events(self):
        """Index events for faster lookup"""
        for event in self.existing_events:
            # Index by composite key
            composite_key = self.create_composite_key(event)
            if composite_key not in self.indexed_events:
                self.indexed_events[composite_key] = []
            self.indexed_events[composite_key].append(event)

            # Index by content hash
            content_hash = self.create_content_hash(event)
            self.content_hashes[content_hash] = event

    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        if not title:
            return ""
        normalized = re.sub(r"\s+", " ", title.strip().lower())
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\bwith\b|\band\b|\bfeat\b|\bfeaturing\b", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def normalize_venue(self, venue_name: str) -> str:
        """Normalize venue name for comparison"""
        if not venue_name:
            return ""
        return venue_name.strip().lower()

    def create_composite_key(self, event: Dict) -> str:
        """Create composite key: normalized_title|venue|date"""
        title = self.normalize_title(event.get("title", ""))
        venue = self.normalize_venue(
            event.get("venue") or event.get("place", {}).get("name", "")
        )

        start_time = event.get("start_datetime", 0)
        if isinstance(start_time, (int, float)):
            date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")
        else:
            date = str(start_time)[:10]

        return f"{title}|{venue}|{date}"

    def create_content_hash(self, event: Dict) -> str:
        """Create content hash for exact duplicate detection"""
        content = {
            "title": self.normalize_title(event.get("title", "")),
            "venue": self.normalize_venue(
                event.get("venue") or event.get("place", {}).get("name", "")
            ),
            "start_time": event.get("start_datetime", 0),
            "description": event.get("description", "").strip()[:200],
        }
        return hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def titles_are_similar(self, title1: str, title2: str, threshold=0.8) -> bool:
        """Check title similarity using fuzzy matching"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)

        if norm1 == norm2:
            return True

        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold

    def is_duplicate(self, new_event: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """
        Check if event is a duplicate
        Returns: (is_duplicate, match_type, existing_event_or_None)
        """
        # 1. Exact content match
        content_hash = self.create_content_hash(new_event)
        if content_hash in self.content_hashes:
            return True, "exact_content_match", self.content_hashes[content_hash]

        # 2. Composite key match
        composite_key = self.create_composite_key(new_event)
        if composite_key in self.indexed_events:
            candidates = self.indexed_events[composite_key]

            if len(candidates) == 1:
                return True, "composite_key_match", candidates[0]

            # Multiple candidates - check title similarity
            new_title = new_event.get("title", "")
            for candidate in candidates:
                if self.titles_are_similar(new_title, candidate.get("title", "")):
                    return True, "similar_title_match", candidate

        # 3. Fuzzy matching across all events
        new_title = new_event.get("title", "")
        new_venue = self.normalize_venue(
            new_event.get("venue") or new_event.get("place", {}).get("name", "")
        )
        new_date = None

        start_time = new_event.get("start_datetime", 0)
        if isinstance(start_time, (int, float)):
            new_date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")

        for existing in self.existing_events:
            existing_venue = self.normalize_venue(
                existing.get("place", {}).get("name", "")
            )
            existing_date = None

            ex_start = existing.get("start_datetime", 0)
            if isinstance(ex_start, (int, float)):
                existing_date = datetime.fromtimestamp(ex_start).strftime("%Y-%m-%d")

            if new_date == existing_date and new_venue == existing_venue:
                if self.titles_are_similar(
                    new_title, existing.get("title", ""), threshold=0.75
                ):
                    return True, "fuzzy_match", existing

        return False, "new_event", None


class VenueValidator:
    def __init__(self):
        self.venue_mappings = {
            "will's pub": {
                "id": 1,
                "name": "Will's Pub",
                "address": "1042 N. Mills Ave. Orlando, FL 32803",
            },
            "wills pub": {
                "id": 1,
                "name": "Will's Pub",
                "address": "1042 N. Mills Ave. Orlando, FL 32803",
            },
            "conduit": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
            "stardust": {
                "id": 4,
                "name": "Stardust Video & Coffee",
                "address": "1842 Winter Park Rd",
            },
            "stardust video & coffee": {
                "id": 4,
                "name": "Stardust Video & Coffee",
                "address": "1842 Winter Park Rd",
            },
            "sly fox": {"id": 6, "name": "Sly Fox", "address": "Not Available"},
        }
        self.default_venue = {
            "id": 1,
            "name": "Will's Pub",
            "address": "1042 N. Mills Ave. Orlando, FL 32803",
        }

    def normalize_venue_name(self, venue_name: str) -> str:
        """Normalize venue name for lookup"""
        if not venue_name:
            return ""
        return venue_name.strip().lower()

    def get_venue_info(self, venue_name: str) -> Dict:
        """Get venue info from mapping or return default"""
        normalized = self.normalize_venue_name(venue_name)
        return self.venue_mappings.get(normalized, self.default_venue)

    def validate_and_fix_venue(self, event: Dict) -> Dict:
        """Validate and fix venue data in event"""
        venue_name = event.get("venue")
        place_id = event.get("place_id")

        if not venue_name:
            # Try to extract from place if available
            if event.get("place") and event["place"].get("name"):
                venue_name = event["place"]["name"]
            else:
                print(
                    f"⚠️ Event missing venue, using default: {event.get('title', 'Unknown')[:40]}..."
                )
                venue_name = self.default_venue["name"]

        # Get correct venue info
        venue_info = self.get_venue_info(venue_name)

        # Update event with validated venue data
        event["venue"] = venue_info["name"]
        event["place_id"] = venue_info["id"]

        # Ensure place object exists for compatibility
        if "place" not in event:
            event["place"] = {
                "id": venue_info["id"],
                "name": venue_info["name"],
                "address": venue_info.get("address", ""),
            }

        return event


class EnhancedGancioSync:
    def __init__(self, gancio_base_url="http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()
        self.authenticated = False
        self.venue_validator = VenueValidator()

    def authenticate(self):
        """Authenticate with Gancio"""
        print("🔑 Authenticating with Gancio...")

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        try:
            # Get login page first
            self.session.get(f"{self.gancio_base_url}/login")

            # Post login credentials
            login_url = f"{self.gancio_base_url}/auth/login"
            response = self.session.post(
                login_url,
                data={"email": email, "password": password},
                allow_redirects=True,
            )

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

    def get_existing_events(self) -> List[Dict]:
        """Get all existing events from Gancio"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Could not fetch existing events: {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️ Error fetching existing events: {e}")
            return []

    def create_event(self, event_data: Dict) -> bool:
        """Create a new event in Gancio"""
        try:
            # Validate and fix venue data
            event_data = self.venue_validator.validate_and_fix_venue(event_data)

            # Prepare event data for Gancio API
            gancio_event = {
                "title": event_data.get("title", ""),
                "description": event_data.get("description", ""),
                "start_datetime": event_data.get("start_datetime", 0),
                "end_datetime": event_data.get("end_datetime", 0),
                "place_id": event_data.get("place_id", 1),
                "tags": event_data.get("tags", []),
            }

            response = self.session.post(
                f"{self.gancio_base_url}/api/event", json=gancio_event
            )

            if response.status_code in [200, 201]:
                print(f"✅ Created event: {event_data.get('title', 'Unknown')[:50]}...")
                return True
            else:
                print(
                    f"❌ Failed to create event: {response.status_code} - {response.text[:100]}"
                )
                return False

        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return False


def scrape_willspub_events() -> List[Dict]:
    """Scrape Will's Pub events"""
    print("📥 Scraping Will's Pub events...")
    # Import and use existing scraper
    try:
        from willspub_scraper import scrape_willspub_events as do_willspub_scrape

        events = do_willspub_scrape()
        print(f"📋 Found {len(events)} Will's Pub events")
        return events
    except ImportError:
        print("⚠️ Will's Pub scraper not available")
        return []
    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []


def scrape_conduit_events() -> List[Dict]:
    """Scrape Conduit events"""
    print("📥 Scraping Conduit events...")
    # Import and use existing scraper
    try:
        from conduit_scraper import scrape_conduit_events as do_conduit_scrape

        events = do_conduit_scrape()
        print(f"📋 Found {len(events)} Conduit events")
        return events
    except ImportError:
        print("⚠️ Conduit scraper not available")
        return []
    except Exception as e:
        print(f"❌ Error scraping Conduit: {e}")
        return []


def main():
    """Main sync function with robust deduplication and venue validation"""
    print("🚀 Starting Enhanced Sync with Complete Validation")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize syncer
    syncer = EnhancedGancioSync()

    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1

    # Get existing events for deduplication
    print("\n📊 Fetching existing events for deduplication...")
    existing_events = syncer.get_existing_events()
    print(f"📋 Found {len(existing_events)} existing events")

    # Initialize deduplicator
    deduplicator = RobustDeduplicator(existing_events)

    # Scrape events from all venues
    all_new_events = []

    # Scrape Will's Pub
    willspub_events = scrape_willspub_events()
    if willspub_events:
        # Ensure venue is set
        for event in willspub_events:
            if not event.get("venue"):
                event["venue"] = "Will's Pub"
        all_new_events.extend(willspub_events)

    # Scrape Conduit
    conduit_events = scrape_conduit_events()
    if conduit_events:
        # Ensure venue is set
        for event in conduit_events:
            if not event.get("venue"):
                event["venue"] = "Conduit"
        all_new_events.extend(conduit_events)

    print(f"\n📥 Scraped {len(all_new_events)} total events from all venues")

    if not all_new_events:
        print("ℹ️ No new events found to process")
        return 0

    # Filter out duplicates using robust deduplication
    print(f"\n🔍 Running robust deduplication...")
    new_events = []
    skipped_events = []
    venue_fixes = 0

    for event in all_new_events:
        # Validate and fix venue first
        original_venue = event.get("venue")
        event = syncer.venue_validator.validate_and_fix_venue(event)
        if original_venue != event.get("venue"):
            venue_fixes += 1

        # Check for duplicates
        is_dup, match_type, existing_event = deduplicator.is_duplicate(event)

        if is_dup:
            skipped_events.append((event, match_type, existing_event))
            print(
                f"⏭️ Skipping duplicate ({match_type}): {event.get('title', 'Unknown')[:40]}..."
            )
        else:
            new_events.append(event)

    # Summary
    print(f"\n📊 Processing Summary:")
    print(f"   📥 Total scraped events: {len(all_new_events)}")
    print(f"   🆕 New events to sync: {len(new_events)}")
    print(f"   ⏭️ Duplicates skipped: {len(skipped_events)}")
    print(f"   🔧 Venue fixes applied: {venue_fixes}")

    # Show details of skipped events
    if skipped_events:
        print(f"\n⏭️ Skipped Events Details:")
        for event, match_type, existing in skipped_events:
            print(f"   • {match_type}: {event.get('title', 'Unknown')[:50]}...")

    # Create new events
    if new_events:
        print(f"\n🚀 Creating {len(new_events)} new events...")
        created_count = 0
        failed_count = 0

        for i, event in enumerate(new_events, 1):
            print(
                f"[{i}/{len(new_events)}] Creating: {event.get('title', 'Unknown')[:40]}..."
            )

            if syncer.create_event(event):
                created_count += 1
            else:
                failed_count += 1

        print(f"\n📊 Creation Results:")
        print(f"   ✅ Successfully created: {created_count}")
        print(f"   ❌ Failed to create: {failed_count}")

        if created_count > 0:
            print(f"🎉 Sync completed successfully!")
        else:
            print(f"⚠️ No events were created")
    else:
        print("\n✨ All events already exist - no new events to create!")

    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
