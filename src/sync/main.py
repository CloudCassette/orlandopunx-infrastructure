#!/usr/bin/env python3
"""
Enhanced Multi-Venue Event Sync with Venue Enforcement
- Robust deduplication
- Mandatory venue assignment for all events
- Special handling for Conduit events
- Comprehensive error handling
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


class VenueEnforcer:
    """Ensures every event has proper venue assignment"""

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
            # Alternative names
            "the conduit": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
            "conduit bar": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
        }

        self.default_venue = {
            "id": 1,
            "name": "Will's Pub",
            "address": "1042 N. Mills Ave. Orlando, FL 32803",
        }

        # Intelligent venue detection patterns
        self.venue_patterns = {
            5: [r"\bconduit\b", r"22.*magnolia", r"downtown.*orlando"],  # Conduit
            1: [r"will\'?s\s*pub", r"1042.*mills", r"mills.*ave"],  # Will's Pub
            4: [r"stardust", r"video.*coffee", r"1842.*winter"],  # Stardust
            6: [r"sly.*fox"],  # Sly Fox
        }

    def normalize_venue_name(self, venue_name: str) -> str:
        """Normalize venue name for lookup"""
        if not venue_name:
            return ""
        return re.sub(r"[^\w\s]", "", venue_name.strip().lower())

    def extract_venue_from_title(self, title: str) -> Optional[str]:
        """Extract venue from event title"""
        if not title:
            return None

        venue_patterns = [
            (r"@\s*([^,\n]+)", 1),  # "Event @ Venue"
            (r"at\s+([^,\n]+)", 1),  # "Event at Venue"
            (r"\b(conduit)\b", 1),  # Conduit mentions
            (r"\b(will\'?s\s*pub)\b", 1),  # Will's Pub mentions
        ]

        for pattern, group in venue_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(group).strip()

        return None

    def detect_venue_from_content(self, event: Dict) -> Optional[Dict]:
        """Intelligently detect venue from event content"""
        text_content = " ".join(
            [
                event.get("title", ""),
                event.get("description", ""),
                str(event.get("venue", "")),
                str(event.get("location", "")),
            ]
        ).lower()

        for venue_id, patterns in self.venue_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_content, re.IGNORECASE):
                    # Find venue info by ID
                    for venue_info in self.venue_mappings.values():
                        if venue_info["id"] == venue_id:
                            return venue_info

        return None

    def get_venue_info(self, venue_name: str, event: Dict = None) -> Dict:
        """Get venue info with intelligent fallback"""
        # Try exact mapping first
        if venue_name:
            normalized = self.normalize_venue_name(venue_name)
            if normalized in self.venue_mappings:
                return self.venue_mappings[normalized]

        # Try intelligent detection from event content
        if event:
            detected_venue = self.detect_venue_from_content(event)
            if detected_venue:
                print(
                    f"🎯 Intelligently detected venue: {detected_venue['name']} for event: {event.get('title', 'Unknown')[:40]}..."
                )
                return detected_venue

        # Fallback to default venue
        return self.default_venue

    def ensure_venue_assignment(self, event_data: Dict) -> Dict:
        """CRITICAL: Ensure every event has a valid venue assignment"""

        # 1. Extract venue from multiple sources (priority order)
        venue_sources = [
            event_data.get("venue"),
            event_data.get("location"),
            (
                event_data.get("place", {}).get("name")
                if isinstance(event_data.get("place"), dict)
                else None
            ),
            self.extract_venue_from_title(event_data.get("title", "")),
            event_data.get("source_venue"),  # For scrapers that set this
        ]

        # 2. Find first valid venue
        venue_name = None
        for source in venue_sources:
            if source and str(source).strip():
                venue_name = str(source).strip()
                break

        # 3. Get venue information (with intelligent detection)
        venue_info = self.get_venue_info(venue_name, event_data)

        # 4. Set all venue-related fields
        event_data["venue"] = venue_info["name"]
        event_data["place_id"] = venue_info["id"]
        event_data["place"] = {
            "id": venue_info["id"],
            "name": venue_info["name"],
            "address": venue_info.get("address", ""),
        }

        # 5. Final validation - this should NEVER fail
        if not event_data.get("place_id") or event_data.get("place_id") == 0:
            print(
                f"🚨 CRITICAL: Event still missing venue after assignment: {event_data.get('title', 'Unknown')}"
            )
            # Force default venue as last resort
            event_data["place_id"] = 1  # Will's Pub
            event_data["venue"] = self.default_venue["name"]
            event_data["place"] = self.default_venue

        return event_data


class RobustDeduplicator:
    """Enhanced deduplication with multiple matching strategies"""

    def __init__(self, existing_events: List[Dict]):
        self.existing_events = existing_events
        self.indexed_events = {}
        self.content_hashes = {}
        self._index_events()

    def _index_events(self):
        """Index events for faster lookup"""
        for event in self.existing_events:
            composite_key = self.create_composite_key(event)
            if composite_key not in self.indexed_events:
                self.indexed_events[composite_key] = []
            self.indexed_events[composite_key].append(event)

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

    def create_composite_key(self, event: Dict) -> str:
        """Create composite key: title|venue|date"""
        title = self.normalize_title(event.get("title", ""))
        venue = event.get("venue") or event.get("place", {}).get("name", "")
        venue = venue.strip().lower()

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
            "venue": (event.get("venue") or event.get("place", {}).get("name", ""))
            .strip()
            .lower(),
            "start_time": event.get("start_datetime", 0),
            "description": event.get("description", "").strip()[:200],
        }
        return hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def titles_are_similar(self, title1: str, title2: str, threshold=0.8) -> bool:
        """Check title similarity"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)

        if norm1 == norm2:
            return True

        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold

    def is_duplicate(self, new_event: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Check if event is duplicate using multiple strategies"""
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

        return False, "new_event", None


class EnhancedGancioSyncWithVenueEnforcement:
    """Enhanced sync with mandatory venue assignment"""

    def __init__(self, gancio_base_url="http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()
        self.authenticated = False
        self.venue_enforcer = VenueEnforcer()

    def authenticate(self):
        """Authenticate with Gancio"""
        print("🔑 Authenticating with Gancio...")

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        try:
            self.session.get(f"{self.gancio_base_url}/login")

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
        """Get all existing events"""
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
        """Create event with mandatory venue validation"""
        try:
            # CRITICAL: Enforce venue assignment before creating event
            event_data = self.venue_enforcer.ensure_venue_assignment(event_data)

            # Final validation - this should never fail after venue enforcement
            if not event_data.get("place_id"):
                raise ValueError(
                    f"🚨 CRITICAL: Event missing venue assignment after enforcement: {event_data.get('title')}"
                )

            # Prepare Gancio API payload
            gancio_event = {
                "title": event_data.get("title", ""),
                "description": event_data.get("description", ""),
                "start_datetime": event_data.get("start_datetime", 0),
                "end_datetime": event_data.get("end_datetime", 0),
                "place_id": event_data["place_id"],  # GUARANTEED to be present
                "tags": event_data.get("tags", []),
            }

            response = self.session.post(
                f"{self.gancio_base_url}/api/event", json=gancio_event
            )

            if response.status_code in [200, 201]:
                venue_name = event_data.get("venue", "Unknown")
                print(
                    f"✅ Created event at {venue_name}: {event_data.get('title', 'Unknown')[:50]}..."
                )
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
    """Scrape Will's Pub events (placeholder for your existing scraper)"""
    print("📥 Scraping Will's Pub events...")
    # Your existing Will's Pub scraper code here
    # For now, return empty list
    try:
        # Import your existing scraper
        # from your_willspub_scraper import scrape_events
        # events = scrape_events()
        events = []  # Placeholder

        # Ensure venue is set for all events
        for event in events:
            if not event.get("venue"):
                event["venue"] = "Will's Pub"
                event["source_venue"] = "Will's Pub"  # Help the venue enforcer

        print(f"📋 Found {len(events)} Will's Pub events")
        return events
    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []


def scrape_conduit_events() -> List[Dict]:
    """Scrape Conduit events with special venue handling"""
    print("📥 Scraping Conduit events...")
    # Your existing Conduit scraper code here
    try:
        # Import your existing scraper
        # from your_conduit_scraper import scrape_events
        # events = scrape_events()
        events = []  # Placeholder

        # CRITICAL: Ensure venue is set for all Conduit events
        for event in events:
            if not event.get("venue"):
                event["venue"] = "Conduit"
                event["source_venue"] = "Conduit"  # Help the venue enforcer
                print(
                    f"🎯 Assigned Conduit venue to: {event.get('title', 'Unknown')[:40]}..."
                )

        print(f"📋 Found {len(events)} Conduit events")
        return events
    except Exception as e:
        print(f"❌ Error scraping Conduit: {e}")
        return []


def main():
    """Main sync function with venue enforcement"""
    print("🚀 Starting Enhanced Sync with Venue Enforcement")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize syncer
    syncer = EnhancedGancioSyncWithVenueEnforcement()

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
    all_new_events.extend(willspub_events)

    # Scrape Conduit (with special venue handling)
    conduit_events = scrape_conduit_events()
    all_new_events.extend(conduit_events)

    print(f"\n📥 Scraped {len(all_new_events)} total events from all venues")

    if not all_new_events:
        print("ℹ️ No new events found to process")
        return 0

    # Process events with venue enforcement and deduplication
    print(f"\n🔍 Processing events with venue enforcement and deduplication...")
    new_events = []
    skipped_events = []
    venue_enforcements = 0

    for event in all_new_events:
        # CRITICAL: Enforce venue assignment BEFORE deduplication
        original_venue = event.get("venue")
        event = syncer.venue_enforcer.ensure_venue_assignment(event)

        if original_venue != event.get("venue"):
            venue_enforcements += 1

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
    print(f"   🏢 Venue enforcements: {venue_enforcements}")

    # Verify all new events have venues
    events_without_venues = [e for e in new_events if not e.get("place_id")]
    if events_without_venues:
        print(
            f"\n🚨 CRITICAL: {len(events_without_venues)} events still missing venues after enforcement!"
        )
        for event in events_without_venues:
            print(f"   - {event.get('title', 'Unknown')}")
        return 1  # Fail if any events lack venues

    # Create new events
    if new_events:
        print(f"\n🚀 Creating {len(new_events)} new events...")
        created_count = 0
        failed_count = 0

        for i, event in enumerate(new_events, 1):
            venue_name = event.get("venue", "Unknown")
            title = event.get("title", "Unknown")
            print(f"[{i}/{len(new_events)}] Creating at {venue_name}: {title[:40]}...")

            if syncer.create_event(event):
                created_count += 1
            else:
                failed_count += 1

        print(f"\n📊 Creation Results:")
        print(f"   ✅ Successfully created: {created_count}")
        print(f"   ❌ Failed to create: {failed_count}")

        # Venue-specific summary
        venue_counts = {}
        for event in new_events[:created_count]:
            venue = event.get("venue", "Unknown")
            venue_counts[venue] = venue_counts.get(venue, 0) + 1

        if venue_counts:
            print(f"\n🏢 Events created by venue:")
            for venue, count in sorted(venue_counts.items()):
                print(f"   {venue}: {count} events")

        if created_count > 0:
            print(f"\n🎉 Sync completed successfully!")
        else:
            print(f"\n⚠️ No events were created")
    else:
        print("\n✨ All events already exist - no new events to create!")

    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
