#!/usr/bin/env python3
"""
🔬 Final Conduit Event Diagnosis
===============================
Comprehensive diagnosis of why Conduit events aren't appearing
"""

import getpass
import json
import os
from datetime import datetime

import requests


def final_diagnosis():
    """Final comprehensive check"""

    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )

    email = "godlessamericarecords@gmail.com"
    password = os.environ.get("GANCIO_PASSWORD")

    if not password:
        print("🔑 Enter Gancio password:")
        password = getpass.getpass()

    print("🔬 FINAL DIAGNOSIS - Conduit Event Issues")
    print("=" * 50)

    # Test with the exact format from the existing Conduit event
    print(f"\n1️⃣ Testing with EXACT format from existing Conduit event...")

    # Use exact format from "Jon Breaks Bad News Live with Fatties" event
    # Based on the JSON we saw: placeId: 5, timestamp format, etc.

    test_datetime = datetime.strptime("2025-08-22 19:00", "%Y-%m-%d %H:%M")
    start_timestamp = int(test_datetime.timestamp())
    end_timestamp = start_timestamp + (4 * 3600)  # 4 hours like existing event

    exact_format_event = {
        "title": "FINAL TEST - Exact Format Copy",
        "start_datetime": start_timestamp,
        "end_datetime": end_timestamp,
        "placeId": 5,  # Exact same as working Conduit event
        "multidate": False,
        "tags": [],  # Empty tags like working event
        "description": "Testing exact format copy",
    }

    # Login to public instance
    login_data = {"email": email, "password": password}
    login_response = session.post(
        "https://orlandopunx.com/login", data=login_data, allow_redirects=True
    )

    if login_response.status_code == 200:
        print("✅ Authenticated")

        print(f"📤 Submitting with exact format:")
        print(json.dumps(exact_format_event, indent=2))

        response = session.post("https://orlandopunx.com/add", json=exact_format_event)
        print(f"📨 Response: {response.status_code}")

        if "success" in response.text.lower() or "evento" in response.text.lower():
            print("✅ Success indication in response")
        else:
            print("⚠️ No clear success indication")
            print(f"Response preview: {response.text[:200]}")

    print(f"\n2️⃣ Checking current event count before/after...")

    # Count events before
    events_before = requests.get("https://orlandopunx.com/api/events")
    if events_before.status_code == 200:
        count_before = len(events_before.json())
        conduit_before = sum(
            1
            for e in events_before.json()
            if e.get("place", {}).get("name") == "Conduit"
        )
        print(f"📊 Events before: {count_before} total, {conduit_before} Conduit")

    # Wait a moment
    import time

    print("⏱️ Waiting 30 seconds...")
    time.sleep(30)

    # Count events after
    events_after = requests.get("https://orlandopunx.com/api/events")
    if events_after.status_code == 200:
        count_after = len(events_after.json())
        conduit_after = sum(
            1
            for e in events_after.json()
            if e.get("place", {}).get("name") == "Conduit"
        )
        print(f"📊 Events after: {count_after} total, {conduit_after} Conduit")

        if count_after > count_before:
            print("✅ Event count increased!")
        else:
            print("❌ No new events appeared")

    print(f"\n3️⃣ SUMMARY OF ATTEMPTS:")
    print(f"   • Submitted 19 events with place_id=3 ❌")
    print(f"   • Submitted 19 events with place_id=5 ❌")
    print(f"   • Submitted to local Gancio ❌")
    print(f"   • Test submissions get 200 responses ✅")
    print(f"   • Will's Pub submissions work ✅")
    print(f"   • Conduit venue exists (ID=5) ✅")

    print(f"\n💡 LIKELY ISSUES:")
    print(f"   1. Events may be auto-rejected due to validation rules")
    print(f"   2. Conduit venue may have different permissions")
    print(f"   3. Events may be in a hidden approval queue")
    print(f"   4. There may be duplicate detection preventing submission")

    print(f"\n🎯 RECOMMENDED SOLUTION:")
    print(f"   Use manual import files created earlier:")
    print(f"   • 19 individual .txt files ready for copy-paste")
    print(f"   • Navigate to admin panel and add events manually")
    print(f"   • This guarantees events will appear correctly")


if __name__ == "__main__":
    final_diagnosis()
