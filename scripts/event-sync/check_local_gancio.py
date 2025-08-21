#!/usr/bin/env python3
"""
🔍 Check Local Gancio Instance
=============================
Check what venues and events exist in the local instance
"""

import getpass
import json
import os

import requests


def check_local_gancio():
    """Check local Gancio instance"""

    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )

    local_url = "http://localhost:13120"

    print(f"🔍 Checking local Gancio at {local_url}")

    # Check if local instance is running
    try:
        response = requests.get(local_url, timeout=5)
        print(f"📡 Local Gancio status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach local Gancio: {e}")
        return

    # Login to local instance
    email = "godlessamericarecords@gmail.com"
    password = os.environ.get("GANCIO_PASSWORD")

    if not password:
        print("🔑 Enter Gancio password:")
        password = getpass.getpass()

    login_data = {"email": email, "password": password}
    login_response = session.post(
        f"{local_url}/login", data=login_data, allow_redirects=True
    )

    print(f"🔐 Local login: {login_response.status_code}")

    if login_response.status_code != 200:
        print("❌ Local login failed")
        return

    print("✅ Local authentication successful")

    # Check venues in local instance
    print(f"\n🏢 Checking venues in local Gancio...")
    places_response = session.get(f"{local_url}/api/places")
    print(f"📍 Places API: {places_response.status_code}")

    if places_response.status_code == 200:
        places_data = places_response.json()
        print(f"🏢 Found {len(places_data)} venues in LOCAL Gancio:")

        conduit_found = False
        for place in places_data:
            place_id = place.get("id")
            name = place.get("name", "No name")
            address = place.get("address", "No address")

            print(f"   • ID {place_id}: {name}")
            print(f"     📍 {address}")

            if "conduit" in name.lower() or "6700 aloma" in address.lower():
                conduit_found = True
                print(f"     ✅ CONDUIT VENUE FOUND!")
            print()

        if not conduit_found:
            print("❌ PROBLEM: Conduit venue NOT found in local Gancio!")
            print("💡 This explains why Conduit events aren't appearing")

    # Check events in local instance
    print(f"\n📋 Checking events in local Gancio...")
    events_response = session.get(f"{local_url}/api/events")
    print(f"📊 Events API: {events_response.status_code}")

    if events_response.status_code == 200:
        events_data = events_response.json()
        print(f"📊 Found {len(events_data)} events in LOCAL Gancio")

        # Group by venue
        venue_counts = {}
        conduit_events = []

        for event in events_data:
            place_name = event.get("place", {}).get("name", "Unknown venue")
            venue_counts[place_name] = venue_counts.get(place_name, 0) + 1

            if "conduit" in place_name.lower():
                conduit_events.append(event)

        print(f"\n📊 Events by venue in LOCAL Gancio:")
        for venue, count in sorted(venue_counts.items()):
            print(f"   • {venue}: {count} events")

        print(f"\n🎸 Conduit events in LOCAL: {len(conduit_events)}")
        for event in conduit_events:
            print(f"   • {event.get('title')} | ID: {event.get('id')}")


if __name__ == "__main__":
    check_local_gancio()
