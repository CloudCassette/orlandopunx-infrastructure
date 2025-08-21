#!/usr/bin/env python3
"""
Check if events are being submitted as anonymous events
"""

import json
from datetime import datetime

import requests


def check_event_status():
    print("🔍 CHECKING EVENT SUBMISSION STATUS")
    print("=" * 50)

    base_url = "http://localhost:13120"

    # Check total event count first
    try:
        response = requests.get(f"{base_url}/api/events")
        all_events = response.json() if response.status_code == 200 else []
        print(f"📊 Total events in API: {len(all_events)}")

        # Check for our test event specifically
        test_events = [e for e in all_events if "TEST EVENT" in e.get("title", "")]
        if test_events:
            test_event = test_events[0]
            print(f"🧪 Test event found:")
            print(f"   ID: {test_event.get('id')}")
            print(f"   Title: {test_event.get('title')}")
            print(f"   is_visible: {test_event.get('is_visible', 'not set')}")
            print(f"   userId: {test_event.get('userId', 'not set')}")

            # Print full event data for debugging
            print(f"\n📋 Full test event data:")
            for key, value in test_event.items():
                if key not in ["media", "place"]:  # Skip large objects
                    print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ Error checking events: {e}")

    print(f"\n💡 WHAT TO LOOK FOR IN ADMIN PANEL:")
    print("Based on the 'anonymous users' message, try:")
    print("1. 🔍 Look for filter options in the Events section")
    print("2. 🔍 Check if there's a 'Show all' or 'Show pending' toggle")
    print("3. 🔍 Look for events with 'is_visible: false'")
    print("4. 🔍 Check the MODERATION tab (visible in your screenshot)")
    print("5. 🔍 The test event we just created should be there")


if __name__ == "__main__":
    check_event_status()
