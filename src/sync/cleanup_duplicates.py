#!/usr/bin/env python3
"""
Cleanup Existing Duplicates in Gancio
=====================================

This script identifies and removes duplicate events that are currently
clogging up the approval queue in Gancio admin.
"""

import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests


class GancioDuplicateCleanup:
    """Clean up existing duplicates in Gancio database"""

    def __init__(self, gancio_base_url: str = "http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()
        self.authenticated = False

        # Setup session headers
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

    def authenticate(self) -> bool:
        """Authenticate with Gancio"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        print(f"🔑 Authenticating with Gancio as {email}...")

        try:
            # Get login page first
            self.session.get(f"{self.gancio_base_url}/login")

            # Post credentials
            login_response = self.session.post(
                f"{self.gancio_base_url}/auth/login",
                data={"email": email, "password": password},
                allow_redirects=True,
            )

            if "admin" in login_response.url or login_response.status_code == 200:
                print("✅ Authentication successful")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {login_response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_all_events(self) -> List[Dict]:
        """Get all events from Gancio (including pending approval)"""
        try:
            # Try to get all events including pending ones
            # This might require admin API access
            response = self.session.get(f"{self.gancio_base_url}/api/events?all=true")
            if response.status_code == 200:
                return response.json()

            # Fallback to regular events API
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Could not fetch events: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []

    def create_event_signature(self, event: Dict) -> str:
        """Create a signature for event deduplication"""
        # Normalize key fields
        title = self._normalize_text(event.get("title", ""))
        venue = self._normalize_text(
            event.get("place", {}).get("name", "") or event.get("venue", "")
        )

        # Use date only (not full timestamp) for grouping
        start_time = event.get("start_datetime", 0)
        if isinstance(start_time, (int, float)):
            date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")
        else:
            date = str(start_time)[:10]

        return f"{title}|{venue}|{date}"

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        import re

        # Remove extra whitespace, convert to lowercase
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        # Remove special characters that might vary
        normalized = re.sub(r"[^\w\s]", "", normalized)
        return normalized

    def find_duplicate_groups(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Find groups of duplicate events"""
        signature_groups = defaultdict(list)

        for event in events:
            signature = self.create_event_signature(event)
            signature_groups[signature].append(event)

        # Filter to only groups with duplicates
        duplicates = {
            sig: events_list
            for sig, events_list in signature_groups.items()
            if len(events_list) > 1
        }

        return duplicates

    def analyze_duplicates(self) -> Dict:
        """Analyze duplicate situation"""
        if not self.authenticated:
            print("❌ Must authenticate first")
            return {}

        print("📊 Fetching all events for duplicate analysis...")
        events = self.get_all_events()

        if not events:
            print("⚠️ No events found")
            return {}

        print(f"📋 Found {len(events)} total events")

        duplicate_groups = self.find_duplicate_groups(events)

        print(f"\n🔍 Duplicate Analysis Results:")
        print(f"   Total events: {len(events)}")
        print(f"   Duplicate groups: {len(duplicate_groups)}")

        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print(f"   Extra events to remove: {total_duplicates}")

        return {
            "total_events": len(events),
            "duplicate_groups": len(duplicate_groups),
            "events_to_remove": total_duplicates,
            "groups": duplicate_groups,
        }

    def preview_cleanup(self) -> bool:
        """Preview what would be cleaned up"""
        analysis = self.analyze_duplicates()

        if not analysis.get("groups"):
            print("✨ No duplicates found!")
            return True

        print(f"\n🔍 PREVIEW: Events that would be removed:")
        print("=" * 60)

        for signature, events_group in analysis["groups"].items():
            # Sort by ID to keep the oldest
            events_sorted = sorted(events_group, key=lambda x: x.get("id", 0))
            keep_event = events_sorted[0]
            remove_events = events_sorted[1:]

            print(f"\n📌 Event Group: {signature}")
            print(f"   ✅ KEEP: [{keep_event['id']}] {keep_event['title'][:60]}...")

            for remove_event in remove_events:
                print(
                    f"   ❌ REMOVE: [{remove_event['id']}] {remove_event['title'][:60]}..."
                )

        return True

    def cleanup_duplicates(self, dry_run: bool = True) -> bool:
        """Clean up duplicate events"""
        analysis = self.analyze_duplicates()

        if not analysis.get("groups"):
            print("✨ No duplicates found!")
            return True

        if dry_run:
            print("\n🔍 DRY RUN MODE - No actual deletions will be performed")
            return self.preview_cleanup()

        print(
            f"\n🗑️ CLEANUP: Removing {analysis['events_to_remove']} duplicate events..."
        )
        print("⚠️ THIS WILL PERMANENTLY DELETE EVENTS!")

        # Confirmation prompt
        confirmation = input("\nType 'DELETE' to confirm removal of duplicates: ")
        if confirmation != "DELETE":
            print("❌ Cleanup cancelled")
            return False

        removed_count = 0
        error_count = 0

        for signature, events_group in analysis["groups"].items():
            # Sort by ID to keep the oldest
            events_sorted = sorted(events_group, key=lambda x: x.get("id", 0))
            keep_event = events_sorted[0]
            remove_events = events_sorted[1:]

            print(f"\n📌 Processing: {signature}")
            print(f"   ✅ Keeping: [{keep_event['id']}] {keep_event['title'][:50]}...")

            for remove_event in remove_events:
                event_id = remove_event["id"]
                try:
                    # Delete event via API
                    delete_response = self.session.delete(
                        f"{self.gancio_base_url}/api/event/{event_id}"
                    )

                    if delete_response.status_code in [200, 204, 404]:
                        print(f"   ✅ Removed: [{event_id}]")
                        removed_count += 1
                    else:
                        print(
                            f"   ❌ Failed to remove [{event_id}]: {delete_response.status_code}"
                        )
                        error_count += 1

                except Exception as e:
                    print(f"   ❌ Error removing [{event_id}]: {e}")
                    error_count += 1

        print(f"\n📊 Cleanup Summary:")
        print(f"   ✅ Successfully removed: {removed_count}")
        print(f"   ❌ Errors: {error_count}")

        if removed_count > 0:
            print(f"\n🎉 Cleanup completed! Removed {removed_count} duplicate events")

        return error_count == 0


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up duplicate events in Gancio")
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze duplicates without taking action",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview what would be cleaned up (dry run)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Actually perform cleanup (requires confirmation)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)",
    )

    args = parser.parse_args()

    if not any([args.analyze, args.preview, args.cleanup]):
        print("❌ Must specify one of: --analyze, --preview, or --cleanup")
        parser.print_help()
        return 1

    print("🧹 Gancio Duplicate Cleanup Tool")
    print("=================================")

    cleaner = GancioDuplicateCleanup()

    if not cleaner.authenticate():
        return 1

    try:
        if args.analyze:
            cleaner.analyze_duplicates()
        elif args.preview:
            cleaner.preview_cleanup()
        elif args.cleanup:
            success = cleaner.cleanup_duplicates(dry_run=not args.force)
            return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
