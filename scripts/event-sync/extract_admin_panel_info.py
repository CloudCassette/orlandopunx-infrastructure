#!/usr/bin/env python3
"""
🔍 Extract Admin Panel Information
=================================
Extract detailed info from the admin panel HTML
"""

import getpass
import json
import os
import re

import requests


def extract_admin_info():
    """Extract info from admin panel"""

    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )

    email = "godlessamericarecords@gmail.com"
    password = os.environ.get("GANCIO_PASSWORD")

    if not password:
        print("🔑 Enter Gancio password:")
        password = getpass.getpass()

    # Login
    login_data = {"email": email, "password": password}
    login_response = session.post(
        "https://orlandopunx.com/login", data=login_data, allow_redirects=True
    )

    if login_response.status_code != 200:
        print("❌ Login failed")
        return

    # Get admin panel
    admin_response = session.get("https://orlandopunx.com/admin")

    if admin_response.status_code == 200:
        html_content = admin_response.text
        print("✅ Admin panel accessed")

        # Look for events in the HTML
        print(f"\n🔍 Searching for 'Horror Trivia' in admin panel...")
        if "Horror Trivia" in html_content:
            print("✅ Found 'Horror Trivia' in admin HTML!")
        else:
            print("❌ 'Horror Trivia' NOT found in admin HTML")

        # Look for other Conduit event titles
        conduit_titles = [
            "Horror Trivia",
            "Void. Terror. Silence",
            "AJ McQueen",
            "Impending Doom",
            "Hopes and Dreams",
        ]

        found_titles = []
        for title in conduit_titles:
            if title in html_content:
                found_titles.append(title)

        print(f"\n📝 Conduit event titles found in admin: {len(found_titles)}")
        for title in found_titles:
            print(f"   ✅ {title}")

        # Look for queue/pending indicators
        queue_indicators = ["queue", "pending", "approval", "moderate", "review"]
        found_indicators = []
        for indicator in queue_indicators:
            if indicator in html_content.lower():
                found_indicators.append(indicator)

        print(f"\n⏳ Queue indicators found: {found_indicators}")

        # Extract JavaScript data if present
        if "window.__NUXT__" in html_content:
            print(f"\n🔍 Extracting JavaScript data...")

            # Look for events in the JS data
            js_match = re.search(r"window\.__NUXT__=.*", html_content)
            if js_match:
                js_content = js_match.group(0)

                # Count mentions of our event titles
                for title in conduit_titles:
                    if title in js_content:
                        print(f"   ✅ Found '{title}' in JavaScript data")

        # Check if there are form elements for adding events
        if "form" in html_content.lower() and "event" in html_content.lower():
            print(f"\n📝 Admin panel has event forms - admin functionality available")

        # Check admin menu/navigation
        if "Places" in html_content or "Events" in html_content:
            print(f"\n📋 Admin navigation found")

        # Look for specific admin sections
        admin_sections = re.findall(r'href="([^"]*admin[^"]*)"', html_content)
        if admin_sections:
            print(f"\n🔗 Admin sections found:")
            for section in set(admin_sections):
                print(f"   • {section}")

    else:
        print(f"❌ Admin panel failed: {admin_response.status_code}")


if __name__ == "__main__":
    extract_admin_info()
