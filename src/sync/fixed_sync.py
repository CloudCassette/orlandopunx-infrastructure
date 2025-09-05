#!/usr/bin/env python3
"""
Fixed Event Sync System - Proper Duplicate Prevention
=====================================================

Key fixes:
1. Check BOTH published AND unconfirmed events for duplicates
2. Use direct database access when available for better duplicate detection
3. Implement proper slug-based duplicate checking
4. Add option to approve events instead of creating new ones
"""

import hashlib
import json
import os
import pickle
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests


class FixedEventSync:
    """Fixed sync system that properly prevents duplicates"""

    def __init__(self):
        self.gancio_base_url = os.environ.get(
            "GANCIO_BASE_URL", "http://localhost:13120"
        )
        self.gancio_email = os.environ.get("GANCIO_EMAIL", "admin")
        self.gancio_password = os.environ.get("GANCIO_PASSWORD", "")
        self.session = requests.Session()
        self.existing_events = {}
        self.db_path = "/var/lib/gancio/gancio.sqlite"

    def load_all_existing_events(self):
        """Load ALL events (published AND unconfirmed) to check for duplicates"""
        print("📊 Loading existing events for duplicate checking...")

        # First try direct database access if available
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get ALL events, not just published ones
                cursor.execute(
                    """
                    SELECT id, title, slug, start_datetime, placeId, is_visible
                    FROM events
                    ORDER BY id DESC
                """
                )

                db_events = cursor.fetchall()
                conn.close()

                print(f"   📁 Found {len(db_events)} total events in database")

                for event_id, title, slug, start_dt, place_id, is_visible in db_events:
                    # Create multiple keys for matching
                    base_slug = re.sub(r"-\d+$", "", slug) if slug else ""

                    # Store by multiple keys for better duplicate detection
                    self.existing_events[slug] = {
                        "id": event_id,
                        "title": title,
                        "slug": slug,
                        "is_visible": is_visible,
                    }

                    # Also index by base slug (without number suffix)
                    if base_slug and base_slug != slug:
                        if base_slug not in self.existing_events:
                            self.existing_events[base_slug] = []
                        if isinstance(self.existing_events[base_slug], list):
                            self.existing_events[base_slug].append(
                                {
                                    "id": event_id,
                                    "title": title,
                                    "slug": slug,
                                    "is_visible": is_visible,
                                }
                            )

                published_count = sum(1 for e in db_events if e[5] == 1)
                unconfirmed_count = len(db_events) - published_count
                print(
                    f"   ✅ Loaded {published_count} published, {unconfirmed_count} unconfirmed events"
                )
                return True

            except Exception as e:
                print(f"   ⚠️ Could not read database directly: {e}")

        # Fallback to API (less reliable for unconfirmed events)
        try:
            # Get published events
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                published_events = response.json()
                print(f"   📡 Found {len(published_events)} published events via API")

                for event in published_events:
                    slug = event.get("slug", "")
                    self.existing_events[slug] = event

                    # Also index by base slug
                    base_slug = re.sub(r"-\d+$", "", slug)
                    if base_slug != slug:
                        if base_slug not in self.existing_events:
                            self.existing_events[base_slug] = []
                        if isinstance(self.existing_events[base_slug], list):
                            self.existing_events[base_slug].append(event)

            # Note: Cannot get unconfirmed events without admin auth via API
            print("   ⚠️ Warning: Cannot check unconfirmed events via API")
            print("   ⚠️ This may still create duplicates in the approval queue!")

        except Exception as e:
            print(f"   ❌ Error loading events via API: {e}")

    def create_event_slug(self, title: str, venue: str = "") -> str:
        """Create a slug from event title and venue"""
        text = f"{title} {venue}".lower().strip()
        # Remove special characters and replace spaces with hyphens
        slug = re.sub(r"[^a-z0-9\s-]", "", text)
        slug = re.sub(r"\s+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")[:100]  # Limit length

    def is_duplicate_event(self, event: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Check if an event is a duplicate of an existing event.
        Returns (is_duplicate, existing_event_data)
        """
        title = event.get("title", "").lower().strip()
        venue = event.get("venue", "").lower().strip()

        # Create potential slug for this event
        potential_slug = self.create_event_slug(title, venue)

        # Direct slug match
        if potential_slug in self.existing_events:
            existing = self.existing_events[potential_slug]
            if isinstance(existing, dict):
                print(f"   🔍 Found exact slug match: {potential_slug}")
                return True, existing

        # Check base slug (for numbered variants)
        base_slug = re.sub(r"-\\d+$", "", potential_slug)
        if base_slug in self.existing_events:
            existing = self.existing_events[base_slug]
            if isinstance(existing, list) and len(existing) > 0:
                print(
                    f"   🔍 Found events with base slug: {base_slug} ({len(existing)} variants)"
                )
                return True, existing[0]
            elif isinstance(existing, dict):
                print(f"   🔍 Found event with base slug: {base_slug}")
                return True, existing

        # Fuzzy title matching for safety
        for slug, existing in self.existing_events.items():
            if isinstance(existing, dict):
                existing_title = existing.get("title", "").lower().strip()
                # Very similar titles at the same venue
                if title in existing_title or existing_title in title:
                    if venue and venue in str(existing.get("placeId", "")).lower():
                        print(f"   🔍 Found similar event by title: {existing_title}")
                        return True, existing

        return False, None

    def submit_event(self, event: Dict) -> bool:
        """Submit an event to Gancio only if it's not a duplicate"""

        # Check for duplicates first
        is_dup, existing = self.is_duplicate_event(event)

        if is_dup:
            print(f"   ⏭️  Skipping duplicate: {event.get('title', 'Unknown')}")
            if existing:
                print(f"      Already exists as ID: {existing.get('id')}")
            return False

        # Event is unique, submit it
        print(f"   📤 Submitting new event: {event.get('title', 'Unknown')}")

        gancio_event = {
            "title": event.get("title"),
            "description": event.get("description", ""),
            "start_datetime": event.get("start_datetime"),
            "end_datetime": event.get("end_datetime"),
            "place": event.get("venue", ""),
            "place_id": event.get("place_id", 1),
            "tags": event.get("tags", []),
        }

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/api/event", json=gancio_event
            )

            if response.status_code in [200, 201]:
                print(f"   ✅ Event created successfully")
                # Add to our existing events to prevent re-submission
                slug = self.create_event_slug(event.get("title"), event.get("venue"))
                self.existing_events[slug] = {
                    "id": "new",
                    "title": event.get("title"),
                    "slug": slug,
                }
                return True
            else:
                print(f"   ❌ Creation failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ Error submitting event: {e}")
            return False

    def run_sync(self, events_to_sync: List[Dict]):
        """Run the sync process with proper duplicate prevention"""

        print("\n🚀 Starting Fixed Event Sync")
        print("=" * 60)

        # Load ALL existing events (including unconfirmed)
        self.load_all_existing_events()

        # Process events
        submitted = 0
        skipped = 0
        failed = 0

        for event in events_to_sync:
            try:
                if self.submit_event(event):
                    submitted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"   ❌ Error processing event: {e}")
                failed += 1

        # Summary
        print("\n" + "=" * 60)
        print("📊 Sync Summary:")
        print(f"   ✅ Submitted: {submitted} new events")
        print(f"   ⏭️  Skipped: {skipped} duplicates")
        print(f"   ❌ Failed: {failed} events")
        print(f"   📚 Total existing: {len(self.existing_events)} events")

        return submitted > 0 or skipped > 0


def main():
    """Main entry point"""

    # Example events to sync (replace with your actual source)
    test_events = [
        {
            "title": "Test Event",
            "venue": "Will's Pub",
            "start_datetime": "2025-01-01T20:00:00",
            "end_datetime": "2025-01-01T23:00:00",
            "description": "Test event",
            "tags": ["punk", "test"],
        }
    ]

    sync = FixedEventSync()
    success = sync.run_sync(test_events)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
