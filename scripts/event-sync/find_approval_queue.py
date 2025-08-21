#!/usr/bin/env python3
"""
🔍 Find Gancio Approval Queue - Comprehensive Diagnostic
======================================================
This will help locate exactly where events go for approval
"""

import getpass
import json
import os
from datetime import datetime

import requests


def find_approval_queue():
    base_url = "https://orlandopunx.com"

    print("🔍 FINDING GANCIO APPROVAL QUEUE")
    print("=" * 50)

    # Get admin credentials
    email = "godlessamericarecords@gmail.com"
    password = os.getenv("GANCIO_PASSWORD") or getpass.getpass(
        "Enter your Gancio password: "
    )

    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )

    # Step 1: Authenticate using web form (like working script)
    print(f"🔑 Authenticating as {email}...")

    try:
        login_data = {"email": email, "password": password}

        response = session.post(
            f"{base_url}/login", data=login_data, allow_redirects=True
        )

        if response.status_code == 200:
            print("✅ Web authentication successful!")
        else:
            print(f"❌ Web authentication failed: {response.status_code}")
            return

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return

    # Step 2: Test various API endpoints with authentication
    print("\n🔍 Testing API endpoints with authentication...")

    endpoints_to_test = [
        ("/api/events", "All events"),
        ("/api/events?status=pending", "Pending events"),
        ("/api/events?status=draft", "Draft events"),
        ("/api/events?approved=true", "Approved events"),
        ("/api/events?approved=false", "Unapproved events"),
        ("/api/events/admin", "Admin events"),
        ("/api/admin/events", "Admin events alt"),
        ("/api/events/pending", "Pending events alt"),
        ("/api/events/drafts", "Draft events alt"),
        ("/api/user/events", "User events"),
        ("/api/moderator/events", "Moderator events"),
    ]

    results = {}

    for endpoint, description in endpoints_to_test:
        try:
            response = session.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    results[endpoint] = {
                        "count": len(data),
                        "description": description,
                        "data": data[:3],  # First 3 items for inspection
                    }
                    print(f"✅ {endpoint}: {len(data)} {description}")
                else:
                    print(f"✅ {endpoint}: non-list response")
            elif response.status_code == 401:
                print(f"🔐 {endpoint}: unauthorized")
            elif response.status_code == 403:
                print(f"🚫 {endpoint}: forbidden")
            elif response.status_code == 404:
                print(f"❌ {endpoint}: not found")
            else:
                print(f"⚠️  {endpoint}: {response.status_code}")

        except Exception as e:
            print(f"❌ {endpoint}: error - {e}")

    # Step 3: Try to create a test event and track its status
    print(f"\n🧪 Creating test event to see approval workflow...")

    test_event = {
        "title": f'TEST EVENT {datetime.now().strftime("%H:%M")} - DELETE ME',
        "description": "This is a test event to trace the approval workflow",
        "start_datetime": int(datetime(2025, 8, 30, 20, 0).timestamp()),
        "end_datetime": int(datetime(2025, 8, 30, 23, 0).timestamp()),
        "place_id": 1,  # Will's Pub
    }

    try:
        response = session.post(f"{base_url}/api/event", json=test_event)
        print(f"Test event creation: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code in [200, 201]:
            print("✅ Test event created!")

            # Check where it appears
            print("\n🔍 Checking where test event appears...")
            for endpoint, info in results.items():
                try:
                    response = session.get(f"{base_url}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        test_events = [
                            e for e in data if "TEST EVENT" in e.get("title", "")
                        ]
                        if test_events:
                            print(f"🎯 Test event found in: {endpoint}")
                            test_event = test_events[0]
                            print(
                                f"   Status: {test_event.get('status', 'no status field')}"
                            )
                            print(
                                f"   Approved: {test_event.get('approved', 'no approved field')}"
                            )
                            print(f"   ID: {test_event.get('id')}")
                except:
                    continue

        else:
            print(f"❌ Test event creation failed")

    except Exception as e:
        print(f"❌ Test event error: {e}")

    # Step 4: Summary and recommendations
    print(f"\n💡 DIAGNOSIS AND RECOMMENDATIONS:")
    print("=" * 50)

    if results:
        max_events = max([info["count"] for info in results.values()])
        main_endpoint = [
            ep for ep, info in results.items() if info["count"] == max_events
        ][0]

        print(f"📊 Main events endpoint: {main_endpoint} ({max_events} events)")

        # Check for approval workflow indicators
        approval_endpoints = [
            ep
            for ep in results.keys()
            if "pending" in ep or "draft" in ep or "admin" in ep
        ]

        if approval_endpoints:
            print(f"🔍 Potential approval endpoints: {', '.join(approval_endpoints)}")
        else:
            print("⚡ No separate approval endpoints found - likely auto-approved")

    print(f"\n🎯 LIKELY EXPLANATION:")
    print("Your Gancio is probably configured for:")
    print("1. ✅ Auto-approval of submitted events, OR")
    print("2. ✅ Trusted user auto-approval, OR")
    print("3. 🔍 Different admin interface layout")

    print(f"\n📋 TO FIND APPROVAL QUEUE IN ADMIN PANEL:")
    print("Look for these sections after logging in:")
    print("• 'Events' > 'Pending' or 'Draft'")
    print("• 'Moderation' section")
    print("• 'Admin' > 'Events'")
    print("• Filter by status: 'Pending', 'Draft', 'Unapproved'")
    print("• Check user permissions - you might need moderator/admin role")


if __name__ == "__main__":
    find_approval_queue()
