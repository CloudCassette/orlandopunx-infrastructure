#!/usr/bin/env python3
"""
Find ALL Pending Events in Gancio
=================================
This script aggressively tries to find all pending events using multiple methods
"""

import json
import os
import re

import requests
from bs4 import BeautifulSoup


def investigate_gancio_admin():
    """Investigate Gancio admin interface for pending events"""

    # Setup session
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )

    # Authenticate
    email = "godlessamericarecords@gmail.com"
    password = os.getenv("GANCIO_PASSWORD")

    if not password:
        print("❌ GANCIO_PASSWORD environment variable required")
        return

    print("🔑 Authenticating...")

    # Try both local and public URLs
    base_urls = ["http://localhost:13120", "https://orlandopunx.com"]

    for base_url in base_urls:
        try:
            response = session.post(
                f"{base_url}/login",
                data={"email": email, "password": password},
                allow_redirects=True,
            )
            if response.status_code == 200:
                print(f"✅ Authenticated with {base_url}")
                break
        except:
            continue
    else:
        print("❌ Authentication failed with all URLs")
        return

    print("\n🔍 COMPREHENSIVE SEARCH FOR PENDING EVENTS")
    print("=" * 50)

    # Method 1: Try various API endpoints with pagination
    print("\n📡 API EXPLORATION:")

    api_patterns = [
        "/api/events?all=true",
        "/api/events",
        "/api/events?status=pending",
        "/api/events?approved=false",
        "/api/events?draft=true",
        "/api/events?visible=false",
    ]

    all_events = set()  # Use set to avoid duplicates

    for pattern in api_patterns:
        for page in range(1, 11):  # Try first 10 pages
            for limit in [10, 50, 100, 1000]:
                endpoints = [
                    f"{pattern}&page={page}&limit={limit}",
                    f"{pattern}&offset={page*limit}&limit={limit}",
                    f"{pattern}&start={page*limit}&count={limit}",
                ]

                for endpoint in endpoints:
                    try:
                        response = session.get(f"{base_url}{endpoint}")
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list) and data:
                                new_events = len(
                                    [
                                        e
                                        for e in data
                                        if e.get("id")
                                        not in [
                                            existing.get("id")
                                            for existing in all_events
                                        ]
                                    ]
                                )
                                if new_events > 0:
                                    print(
                                        f"  ✅ {endpoint}: {len(data)} events ({new_events} new)"
                                    )
                                    all_events.update(
                                        json.dumps(e, sort_keys=True) for e in data
                                    )
                                    if len(data) == limit:  # Might be more pages
                                        continue
                                    else:
                                        break  # No more pages
                                else:
                                    break  # No new events found
                    except:
                        continue

    # Convert back to list of dicts
    all_events_list = [json.loads(e) for e in all_events]
    print(f"\n📊 Total unique events found via API: {len(all_events_list)}")

    # Method 2: Admin interface scraping
    print("\n🕸️ ADMIN INTERFACE SCRAPING:")

    admin_urls = [
        "/admin",
        "/admin/events",
        "/admin/events/pending",
        "/admin/events/draft",
        "/admin/moderation",
        "/admin/queue",
    ]

    admin_events = []

    for admin_url in admin_urls:
        try:
            response = session.get(f"{base_url}{admin_url}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for event lists in HTML
                event_containers = soup.find_all(
                    ["div", "tr", "li"],
                    string=re.compile(r"(event|title|pending|draft)", re.I),
                )

                print(
                    f"  📋 {admin_url}: {response.status_code} - {len(event_containers)} potential event containers"
                )

                # Look for JSON data in script tags
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.string:
                        # Look for arrays/objects that might contain event data
                        potential_json = re.findall(
                            r"(\[[^\[\]]*\]|\{[^{}]*\})", script.string
                        )
                        for match in potential_json:
                            try:
                                data = json.loads(match)
                                if isinstance(data, (list, dict)):
                                    # Check if it looks like event data
                                    if isinstance(data, list):
                                        event_like = [
                                            item
                                            for item in data
                                            if isinstance(item, dict)
                                            and item.get("title")
                                        ]
                                        if event_like:
                                            admin_events.extend(event_like)
                                    elif isinstance(data, dict) and data.get("title"):
                                        admin_events.append(data)
                            except:
                                continue
        except Exception as e:
            print(f"  ❌ {admin_url}: Error - {e}")

    print(f"📊 Events found via admin scraping: {len(admin_events)}")

    # Method 3: Direct database queries (if possible)
    print("\n💾 DATABASE EXPLORATION:")

    db_endpoints = [
        "/api/admin/events/all",
        "/api/database/events",
        "/api/internal/events",
        "/admin/api/events",
    ]

    for endpoint in db_endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}")
            print(f"  📊 {endpoint}: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"    Found {len(data)} events")
                except:
                    print(f"    Non-JSON response: {len(response.text)} characters")
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")

    # Summary
    print(f"\n🎯 SUMMARY:")
    print(f"📊 Total events found via API: {len(all_events_list)}")
    print(f"🕸️ Events found via admin scraping: {len(admin_events)}")

    if all_events_list:
        print("\n📋 Sample API Events:")
        for i, event in enumerate(all_events_list[:5]):
            print(
                f"  {i+1}. [{event.get('id', 'no-id')}] {event.get('title', 'No title')[:50]}..."
            )

    if admin_events:
        print("\n📋 Sample Admin Events:")
        for i, event in enumerate(admin_events[:5]):
            print(
                f"  {i+1}. [{event.get('id', 'no-id')}] {event.get('title', 'No title')[:50]}..."
            )

    # Find duplicates in the events we found
    if len(all_events_list) > 1:
        print(f"\n🔍 CHECKING FOR DUPLICATES:")
        signatures = {}
        duplicates = []

        for event in all_events_list:
            title = event.get("title", "").lower().strip()
            venue = (
                str(event.get("place", {}).get("name", "") or event.get("venue", ""))
                .lower()
                .strip()
            )

            signature = f"{title}|{venue}"

            if signature in signatures:
                duplicates.append((signatures[signature], event))
            else:
                signatures[signature] = event

        print(f"🔍 Found {len(duplicates)} potential duplicate pairs")

        for orig, dup in duplicates[:3]:  # Show first 3
            print(f"  🔄 '{orig.get('title', '')[:30]}...' appears multiple times")

    print(f"\n💡 RECOMMENDATIONS:")
    if len(all_events_list) == 10:
        print("⚠️ API seems to be limiting results to 10 events")
        print("🔧 You may need to:")
        print("   1. Check Gancio admin interface manually")
        print("   2. Look for pagination controls in the admin UI")
        print("   3. Contact Gancio support about bulk operations")
        print("   4. Check if there are database-level tools available")
    else:
        print("✅ Found more than 10 events - API access seems good")


if __name__ == "__main__":
    investigate_gancio_admin()
