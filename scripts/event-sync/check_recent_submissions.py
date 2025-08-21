#!/usr/bin/env python3
"""
🕐 Check Recent Event Submissions
================================
Looks for recently submitted events that might be pending
"""

import json
from datetime import datetime, timedelta

import requests


def check_recent_events():
    """Check for recent event submissions"""

    print("🕐 Checking for recent event submissions...")

    events_response = requests.get("https://orlandopunx.com/api/events")

    if events_response.status_code == 200:
        events_data = events_response.json()
        print(f"📊 Total events in API: {len(events_data)}")

        # Count by venue
        venue_counts = {}
        conduit_events = []
        recent_events = []

        # Current time for comparison
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        for event in events_data:
            place_name = event.get("place", {}).get("name", "Unknown")
            venue_counts[place_name] = venue_counts.get(place_name, 0) + 1

            # Collect Conduit events
            if "conduit" in place_name.lower():
                conduit_events.append(event)

            # Check for Horror Trivia specifically (first event we submitted)
            title = event.get("title", "")
            if "horror trivia" in title.lower():
                recent_events.append(event)

            # Check for other submitted event titles
            submitted_titles = [
                "void. terror. silence",
                "aj mcqueen",
                "impending doom",
                "hopes and dreams",
                "wyndrider",
                "dark remedy",
            ]

            for submitted_title in submitted_titles:
                if submitted_title in title.lower():
                    recent_events.append(event)
                    break

        print(f"\n📊 Events by venue:")
        for venue, count in sorted(venue_counts.items()):
            print(f"   • {venue}: {count} events")

        print(f"\n🎸 Conduit events found:")
        for event in conduit_events:
            title = event.get("title", "No title")
            event_id = event.get("id")
            place_id = event.get("place", {}).get("id", "unknown")
            print(f"   • ID {event_id}: {title} (place_id: {place_id})")

        print(f"\n🔍 Recently submitted events found:")
        if recent_events:
            for event in recent_events:
                title = event.get("title", "No title")
                venue = event.get("place", {}).get("name", "Unknown")
                event_id = event.get("id")
                print(f"   • ID {event_id}: {title} | {venue}")
        else:
            print("   ❌ None of our submitted events found")

        # Check for Horror Trivia specifically
        horror_events = [
            e for e in events_data if "horror trivia" in e.get("title", "").lower()
        ]
        print(f"\n🎭 Horror Trivia events: {len(horror_events)}")
        for event in horror_events:
            print(f"   • {event.get('title')} | {event.get('place', {}).get('name')}")

    else:
        print(f"❌ Failed to get events: {events_response.status_code}")


if __name__ == "__main__":
    check_recent_events()
