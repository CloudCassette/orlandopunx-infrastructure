#!/usr/bin/env python3
"""
Session-Based Gancio Duplicate Cleanup
======================================
Uses session-based authentication with proper pagination to find and clean up duplicates
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import requests


class GancioSessionCleanup:
    """Clean up duplicates using session-based authentication"""

    def __init__(self, base_url: str = "http://localhost:13120"):
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticated = False

        # Set proper headers
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

    def authenticate(self) -> bool:
        """Authenticate using session-based login"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        print(f"🔑 Authenticating via session as {email}...")

        try:
            # Use the session login that was working
            login_data = {"email": email, "password": password}
            response = self.session.post(
                f"{self.base_url}/login", data=login_data, allow_redirects=True
            )

            if response.status_code == 200:
                self.authenticated = True
                print("✅ Session authentication successful!")
                return True
            else:
                print(f"❌ Session authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_all_events_aggressively(self) -> List[Dict]:
        """Get ALL events using multiple strategies"""
        all_events = []

        print("📊 Fetching all events using aggressive pagination...")

        # Strategy 1: Try documented pagination parameters
        strategies = [
            # Different pagination approaches
            {"params": {"page": 1, "max": 1000}},
            {"params": {"page": 1, "max": 500}},
            {"params": {"page": 1, "max": 100}},
            # Try with different time ranges
            {"params": {"start": 0, "older": True, "max": 1000}},
            {"params": {"start": 0, "end": 9999999999, "max": 1000}},  # Far future
            # Try without pagination limits
            {"params": {}},
            {"params": {"show_multidate": True, "show_recurrent": True}},
        ]

        unique_events = {}  # Use dict to dedupe by ID

        for i, strategy in enumerate(strategies):
            try:
                print(f"  Strategy {i+1}: {strategy['params']}")

                # Try multiple pages for each strategy
                for page in range(1, 21):  # Try up to 20 pages
                    params = strategy["params"].copy()
                    params["page"] = page

                    response = self.session.get(
                        f"{self.base_url}/api/events", params=params
                    )

                    if response.status_code == 200:
                        events = response.json()

                        if not events:
                            print(f"    Page {page}: No events, stopping")
                            break

                        new_count = 0
                        for event in events:
                            event_id = event.get("id")
                            if event_id and event_id not in unique_events:
                                unique_events[event_id] = event
                                new_count += 1

                        print(
                            f"    Page {page}: {len(events)} events ({new_count} new)"
                        )

                        # If no new events or less than expected, likely no more pages
                        if new_count == 0 or len(events) < params.get("max", 100):
                            break
                    else:
                        print(f"    Page {page}: Error {response.status_code}")
                        break

            except Exception as e:
                print(f"    Strategy {i+1} error: {e}")

        all_events = list(unique_events.values())
        print(f"✅ Total unique events found: {len(all_events)}")

        return all_events

    def get_pending_events_aggressively(self) -> List[Dict]:
        """Try to get ALL pending events using multiple approaches"""
        print("🔍 Fetching pending events aggressively...")

        pending_events = {}  # Use dict to dedupe

        # Try different query parameters that might return pending events
        pending_strategies = [
            {"status": "pending"},
            {"status": "draft"},
            {"approved": "false"},
            {"approved": False},
            {"is_active": "false"},
            {"is_active": False},
            {"visible": "false"},
            {"visible": False},
            # Try admin-like endpoints
            {"all": "true", "status": "pending"},
            {"all": True, "status": "pending"},
        ]

        for i, extra_params in enumerate(pending_strategies):
            try:
                print(f"  Strategy {i+1}: {extra_params}")

                # Try multiple pages
                for page in range(1, 11):
                    params = {
                        "page": page,
                        "max": 1000,
                        "start": 0,
                        "older": True,
                        **extra_params,
                    }

                    response = self.session.get(
                        f"{self.base_url}/api/events", params=params
                    )

                    if response.status_code == 200:
                        events = response.json()

                        if not events:
                            break

                        new_count = 0
                        for event in events:
                            event_id = event.get("id")
                            if event_id and event_id not in pending_events:
                                pending_events[event_id] = event
                                new_count += 1

                        print(
                            f"    Page {page}: {len(events)} events ({new_count} new)"
                        )

                        if new_count == 0 or len(events) < 100:
                            break
                    else:
                        if page == 1:  # Only show error for first page
                            print(f"    Error: {response.status_code}")
                        break

            except Exception as e:
                print(f"    Strategy {i+1} error: {e}")

        pending_list = list(pending_events.values())
        print(f"📊 Total unique pending events found: {len(pending_list)}")

        return pending_list

    def create_event_signature(self, event: Dict) -> str:
        """Create a signature for event deduplication"""
        title = self._normalize_text(event.get("title", ""))
        place = event.get("place", {})
        venue = self._normalize_text(place.get("name", "") if place else "")

        # Use date only for grouping
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

        normalized = re.sub(r"\s+", " ", text.strip().lower())
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

    def analyze_all_events(self):
        """Analyze all events for duplicates"""
        print("🔍 ANALYZING ALL EVENTS FOR DUPLICATES")
        print("=" * 50)

        all_events = self.get_all_events_aggressively()

        if not all_events:
            print("⚠️ No events found")
            return {}

        duplicate_groups = self.find_duplicate_groups(all_events)

        print(f"\n📊 DUPLICATE ANALYSIS RESULTS:")
        print(f"   Total events: {len(all_events)}")
        print(f"   Duplicate groups: {len(duplicate_groups)}")

        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print(f"   Events to remove: {total_duplicates}")

        if duplicate_groups:
            print(f"\n🔍 DUPLICATE GROUPS PREVIEW:")
            for i, (signature, events_group) in enumerate(
                list(duplicate_groups.items())[:5]
            ):
                print(f"\n{i+1}. Group: {signature}")
                for j, event in enumerate(events_group):
                    marker = "✅ KEEP" if j == 0 else "❌ REMOVE"
                    print(
                        f"   {marker}: [{event.get('id')}] {event.get('title', 'No title')[:50]}..."
                    )

            if len(duplicate_groups) > 5:
                print(f"\n... and {len(duplicate_groups) - 5} more groups")

        return duplicate_groups

    def analyze_pending_events(self):
        """Analyze pending events specifically"""
        print("🔍 ANALYZING PENDING EVENTS FOR DUPLICATES")
        print("=" * 50)

        pending_events = self.get_pending_events_aggressively()

        if not pending_events:
            print("⚠️ No pending events found")
            return {}

        duplicate_groups = self.find_duplicate_groups(pending_events)

        print(f"\n📊 PENDING DUPLICATE ANALYSIS:")
        print(f"   Total pending events: {len(pending_events)}")
        print(f"   Duplicate groups: {len(duplicate_groups)}")

        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print(f"   Events to remove: {total_duplicates}")

        return duplicate_groups

    def delete_event(self, event_id: int) -> bool:
        """Delete an event using the API"""
        try:
            # Try the documented delete endpoint
            response = self.session.delete(f"{self.base_url}/api/event/{event_id}")
            return response.status_code in [200, 204, 404]
        except:
            return False

    def cleanup_duplicates(self, groups: Dict, dry_run: bool = True) -> bool:
        """Clean up duplicate events"""
        if not groups:
            print("✨ No duplicates to clean up!")
            return True

        total_to_remove = sum(len(group) - 1 for group in groups.values())

        if dry_run:
            print(f"\n🔍 DRY RUN: Would remove {total_to_remove} duplicate events")
            for signature, events_group in list(groups.items())[:3]:
                events_sorted = sorted(events_group, key=lambda x: x.get("id", 999999))
                keep_event = events_sorted[0]
                remove_events = events_sorted[1:]

                print(f"\n📌 {signature}")
                print(
                    f"   ✅ KEEP: [{keep_event.get('id')}] {keep_event.get('title', 'No title')[:50]}..."
                )
                for event in remove_events[:3]:  # Show first 3
                    print(
                        f"   ❌ REMOVE: [{event.get('id')}] {event.get('title', 'No title')[:50]}..."
                    )
            return True

        print(f"\n🗑️ CLEANUP: Removing {total_to_remove} duplicate events...")
        print("⚠️ THIS WILL PERMANENTLY DELETE EVENTS!")

        confirmation = input("\nType 'DELETE' to confirm: ")
        if confirmation != "DELETE":
            print("❌ Cleanup cancelled")
            return False

        removed_count = 0
        error_count = 0

        for signature, events_group in groups.items():
            # Sort by ID to keep the oldest
            events_sorted = sorted(events_group, key=lambda x: x.get("id", 999999))
            keep_event = events_sorted[0]
            remove_events = events_sorted[1:]

            print(f"\n📌 Processing: {signature}")
            print(
                f"   ✅ Keeping: [{keep_event.get('id')}] {keep_event.get('title', 'No title')[:50]}..."
            )

            for event in remove_events:
                event_id = event.get("id")
                if self.delete_event(event_id):
                    print(f"   ✅ Removed: [{event_id}]")
                    removed_count += 1
                else:
                    print(f"   ❌ Failed to remove: [{event_id}]")
                    error_count += 1

        print(f"\n📊 Cleanup Summary:")
        print(f"   ✅ Removed: {removed_count}")
        print(f"   ❌ Errors: {error_count}")

        return error_count == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up duplicates using session-based auth"
    )
    parser.add_argument("--analyze-all", action="store_true", help="Analyze all events")
    parser.add_argument(
        "--analyze-pending", action="store_true", help="Analyze pending events"
    )
    parser.add_argument(
        "--cleanup-pending", action="store_true", help="Clean up pending duplicates"
    )
    parser.add_argument(
        "--cleanup-all", action="store_true", help="Clean up all duplicates"
    )
    parser.add_argument(
        "--force", action="store_true", help="Actually delete (not dry run)"
    )

    args = parser.parse_args()

    if not any(
        [args.analyze_all, args.analyze_pending, args.cleanup_pending, args.cleanup_all]
    ):
        parser.print_help()
        return 1

    print("🧹 Session-Based Gancio Duplicate Cleanup")
    print("=========================================")

    cleaner = GancioSessionCleanup()

    if not cleaner.authenticate():
        return 1

    try:
        if args.analyze_all:
            cleaner.analyze_all_events()

        elif args.analyze_pending:
            cleaner.analyze_pending_events()

        elif args.cleanup_pending:
            groups = cleaner.analyze_pending_events()
            if groups:
                cleaner.cleanup_duplicates(groups, dry_run=not args.force)

        elif args.cleanup_all:
            groups = cleaner.analyze_all_events()
            if groups:
                cleaner.cleanup_duplicates(groups, dry_run=not args.force)

    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
