#!/usr/bin/env python3
"""
Duplicate Event Monitoring System
Monitors for new duplicates and provides alerts
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests


def get_events_from_gancio():
    """Get all events from Gancio API"""
    try:
        response = requests.get("http://localhost:13120/api/events")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch events: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return []


def create_event_signature(event):
    """Create a signature for duplicate detection"""
    title = event.get("title", "").strip().lower()
    venue = event.get("place", {}).get("name", "").strip().lower()

    start_time = event.get("start_datetime", 0)
    if isinstance(start_time, (int, float)):
        date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")
    else:
        date = str(start_time)[:10]

    return f"{title}|{venue}|{date}"


def find_duplicates(events):
    """Find duplicate events"""
    signatures = {}
    duplicates = {}

    for event in events:
        signature = create_event_signature(event)

        if signature not in signatures:
            signatures[signature] = []

        signatures[signature].append(event)

    # Find groups with more than one event
    for signature, event_list in signatures.items():
        if len(event_list) > 1:
            duplicates[signature] = event_list

    return duplicates


def monitor_duplicates():
    """Monitor for duplicates and report"""
    print(f"🔍 Monitoring duplicates at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    events = get_events_from_gancio()
    if not events:
        print("❌ No events found or API error")
        return

    duplicates = find_duplicates(events)

    if duplicates:
        print(f"⚠️ Found {len(duplicates)} duplicate groups:")

        for signature, dup_events in duplicates.items():
            print(f"\n📌 Duplicate Group ({len(dup_events)} events):")
            print(f"   Signature: {signature}")

            for event in dup_events:
                print(f"   - [{event.get('id')}] {event.get('title', 'No title')}")

        # Save report
        report_file = (
            f"duplicate_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(duplicates, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Alert (could be extended to send emails, Slack notifications, etc.)
        total_duplicates = sum(len(events) - 1 for events in duplicates.values())
        print(
            f"\n🚨 ALERT: Found {total_duplicates} duplicate events that should be cleaned up!"
        )

    else:
        print("✅ No duplicates found - all good!")

    return duplicates


def continuous_monitor(interval_minutes=60):
    """Continuously monitor for duplicates"""
    print(
        f"🚀 Starting continuous duplicate monitoring (every {interval_minutes} minutes)"
    )

    while True:
        try:
            duplicates = monitor_duplicates()

            if duplicates:
                # Could trigger additional alerts here
                pass

            print(f"💤 Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(300)  # Wait 5 minutes on error


def cleanup_suggestions(duplicates):
    """Provide cleanup suggestions"""
    if not duplicates:
        print("✅ No duplicates to clean up!")
        return

    print("\n🔧 Cleanup Suggestions:")

    for signature, dup_events in duplicates.items():
        # Sort by ID (keep oldest)
        sorted_events = sorted(dup_events, key=lambda x: x.get("id", 0))

        keep_event = sorted_events[0]
        remove_events = sorted_events[1:]

        print(f"\n📌 Group: {signature}")
        print(
            f"   KEEP: [{keep_event.get('id')}] {keep_event.get('title', 'No title')}"
        )

        for remove_event in remove_events:
            event_id = remove_event.get("id")
            print(f"   REMOVE: [{event_id}] {remove_event.get('title', 'No title')}")
            print(
                f"      Command: curl -X DELETE 'http://localhost:13120/api/event/{event_id}' -H 'Authorization: Bearer YOUR_TOKEN'"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Duplicate Event Monitor")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval", type=int, default=60, help="Monitor interval in minutes"
    )
    parser.add_argument(
        "--suggest-cleanup", action="store_true", help="Show cleanup suggestions"
    )

    args = parser.parse_args()

    if args.continuous:
        continuous_monitor(args.interval)
    else:
        # Single run
        duplicates = monitor_duplicates()

        if args.suggest_cleanup and duplicates:
            cleanup_suggestions(duplicates)
