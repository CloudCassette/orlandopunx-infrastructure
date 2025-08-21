#!/usr/bin/env python3
"""
🏢 Check if Conduit Venue Exists
===============================
Verifies the Conduit venue exists with the expected ID
"""

import json

import requests


def check_venues():
    """Check available venues"""

    print("🔍 Checking available venues...")

    # Check public places API
    places_response = requests.get("https://orlandopunx.com/api/places")
    print(f"📍 Places API response: {places_response.status_code}")

    if places_response.status_code == 200:
        places_data = places_response.json()
        print(f"🏢 Found {len(places_data)} venues:")

        conduit_found = False
        for place in places_data:
            place_id = place.get("id")
            name = place.get("name", "No name")
            address = place.get("address", "No address")

            print(f"   • ID {place_id}: {name}")
            print(f"     📍 {address}")

            if "conduit" in name.lower() or "6700 aloma" in address.lower():
                conduit_found = True
                print(f"     ✅ THIS IS CONDUIT!")
            print()

        if not conduit_found:
            print("❌ Conduit venue NOT found in places API")
            print("💡 This explains why events with place_id=3 don't work!")
        else:
            print("✅ Conduit venue exists")

    else:
        print(f"❌ Failed to get places: {places_response.text}")

    # Also check what events exist
    print(f"\n📋 Checking existing events...")
    events_response = requests.get("https://orlandopunx.com/api/events")

    if events_response.status_code == 200:
        events_data = events_response.json()
        print(f"📊 Found {len(events_data)} public events")

        # Group by venue
        venue_counts = {}
        for event in events_data:
            place_name = event.get("place", {}).get("name", "Unknown venue")
            venue_counts[place_name] = venue_counts.get(place_name, 0) + 1

        print(f"\n📊 Events by venue:")
        for venue, count in sorted(venue_counts.items()):
            print(f"   • {venue}: {count} events")


if __name__ == "__main__":
    check_venues()
