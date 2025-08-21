#!/usr/bin/env python3
"""
🔍 Check Gancio Admin Panel
==========================
Investigates the admin panel to see submitted events
"""

import getpass
import json
import os
from datetime import datetime

import requests


def check_gancio_admin():
    """Check admin panel for events"""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )

    # Use existing credentials
    email = "godlessamericarecords@gmail.com"
    password = os.environ.get("GANCIO_PASSWORD")

    if not password:
        print("🔑 Enter Gancio password:")
        password = getpass.getpass()

    print(f"🔍 Checking Gancio admin panel...")

    # Login
    login_url = "https://orlandopunx.com/api/auth/login"
    login_data = {"email": email, "password": password}

    try:
        response = session.post(login_url, json=login_data)
        print(f"🔐 Login response: {response.status_code}")

        if response.status_code == 200:
            print("✅ Login successful!")

            # Check admin events endpoint
            admin_events_url = "https://orlandopunx.com/api/admin/events"
            events_response = session.get(admin_events_url)
            print(f"📋 Admin events response: {events_response.status_code}")

            if events_response.status_code == 200:
                events_data = events_response.json()
                print(f"📊 Found {len(events_data)} events in admin panel")

                # Look for recent Conduit events
                conduit_events = []
                today = datetime.now().strftime("%Y-%m-%d")

                for event in events_data:
                    if event.get("place", {}).get("name") == "Conduit":
                        conduit_events.append(event)
                    elif "conduit" in event.get("title", "").lower():
                        conduit_events.append(event)

                print(f"🎸 Found {len(conduit_events)} Conduit-related events")

                if conduit_events:
                    print("\n📝 Conduit events found:")
                    for event in conduit_events[:5]:  # Show first 5
                        status = event.get("status", "unknown")
                        title = event.get("title", "No title")
                        place_name = event.get("place", {}).get("name", "No venue")
                        print(f"   • {title} | {place_name} | Status: {status}")
                else:
                    print("❌ No Conduit events found in admin panel")
                    print("\n🔍 Let's check recent events:")
                    recent_events = sorted(
                        events_data, key=lambda x: x.get("created_at", ""), reverse=True
                    )[:10]
                    for event in recent_events:
                        created = event.get("created_at", "unknown")
                        title = event.get("title", "No title")[:50]
                        place_name = event.get("place", {}).get("name", "No venue")
                        status = event.get("status", "unknown")
                        print(f"   • {title} | {place_name} | {status} | {created}")
            else:
                print(f"❌ Failed to get admin events: {events_response.text}")

            # Check places/venues
            places_url = "https://orlandopunx.com/api/admin/places"
            places_response = session.get(places_url)
            print(f"\n🏢 Places response: {places_response.status_code}")

            if places_response.status_code == 200:
                places_data = places_response.json()
                print(f"📍 Found {len(places_data)} venues")

                conduit_place = None
                for place in places_data:
                    if "conduit" in place.get("name", "").lower():
                        conduit_place = place
                        break

                if conduit_place:
                    print(f"🎸 Conduit venue found:")
                    print(f"   ID: {conduit_place.get('id')}")
                    print(f"   Name: {conduit_place.get('name')}")
                    print(f"   Address: {conduit_place.get('address')}")
                else:
                    print("❌ Conduit venue not found")
                    print("\n📍 Available venues:")
                    for place in places_data[:10]:
                        print(
                            f"   • ID {place.get('id')}: {place.get('name')} - {place.get('address', '')[:50]}"
                        )
            else:
                print(f"❌ Failed to get places: {places_response.text}")

        else:
            print(f"❌ Login failed: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_gancio_admin()
