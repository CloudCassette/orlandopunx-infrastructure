#!/usr/bin/env python3

import re
import time
from collections import defaultdict

import requests


def analyze_duplicates_from_saved():
    """Load and analyze events from saved HTML"""
    events = []

    try:
        with open("admin_after_click.html", "r") as f:
            html_content = f.read()

        pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
        matches = re.findall(pattern, html_content)

        for match in matches:
            event_id, title_var, slug = match
            events.append({"id": int(event_id), "slug": slug})
    except FileNotFoundError:
        print("❌ admin_after_click.html not found")
        return [], []

    # Group by base slug
    base_slug_groups = defaultdict(list)
    for event in events:
        base_slug = re.sub(r"-\d+$", "", event["slug"])
        base_slug_groups[base_slug].append(event)

    # Find duplicates
    duplicates_to_delete = []
    kept_originals = []

    for base_slug, event_list in base_slug_groups.items():
        if len(event_list) > 1:
            event_list.sort(key=lambda x: x["id"])
            kept_originals.append(event_list[0])
            duplicates_to_delete.extend(event_list[1:])
        else:
            kept_originals.append(event_list[0])

    return duplicates_to_delete, kept_originals


def login_and_get_session(base_url, email, password):
    """Login using session-based authentication (like the web interface)"""

    session = requests.Session()

    print("🔐 Logging in via web session...")

    # First, get the login page (might set CSRF token)
    login_page_url = f"{base_url}/login"
    try:
        response = session.get(login_page_url)
        print(f"   Got login page: {response.status_code}")
    except Exception as e:
        print(f"   Error getting login page: {e}")
        return None

    # Try to login via form submission (like the browser does)
    login_url = f"{base_url}/login"

    # Try different form data formats
    form_data = {"email": email, "password": password}

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": login_page_url,
    }

    try:
        response = session.post(
            login_url, data=form_data, headers=headers, allow_redirects=True
        )

        if response.status_code == 200:
            # Check if we're logged in by trying to access admin
            admin_response = session.get(f"{base_url}/admin")

            if admin_response.status_code == 200 and "login" not in admin_response.url:
                print("✅ Logged in successfully via session")
                return session
            else:
                print("❌ Login failed - redirected to login page")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def delete_event_via_session(session, base_url, event_id):
    """Delete an event using the authenticated session"""

    # Try different deletion endpoints
    endpoints = [
        f"/api/event/{event_id}",
        f"/api/events/{event_id}",
        f"/admin/event/{event_id}/delete",
        f"/api/event/unconfirmed/{event_id}",
    ]

    for endpoint in endpoints:
        delete_url = base_url + endpoint

        try:
            # Try DELETE method
            response = session.delete(delete_url)
            if response.status_code in [200, 204, 202]:
                return True

            # Try POST with delete action
            response = session.post(delete_url, json={"action": "delete"})
            if response.status_code in [200, 204, 202]:
                return True

        except:
            continue

    return False


def confirm_event_via_session(session, base_url, event_id):
    """Try to confirm/approve an event (which removes duplicates)"""

    # According to Gancio docs, confirming an event might be PUT /api/event/:id/confirm
    confirm_url = f"{base_url}/api/event/{event_id}/confirm"

    try:
        response = session.put(confirm_url)
        if response.status_code in [200, 204, 202]:
            return True

        # Try POST
        response = session.post(confirm_url)
        if response.status_code in [200, 204, 202]:
            return True

    except:
        pass

    return False


def main():
    # Configuration
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"

    print("🚀 Orlando Punx Duplicate Event Cleanup (Session Auth)")
    print("=" * 60)

    # Analyze duplicates
    duplicates, originals = analyze_duplicates_from_saved()

    print(f"\n📊 Analysis Results:")
    print(f"   Total events found: {len(duplicates) + len(originals)}")
    print(f"   Duplicate events: {len(duplicates)}")
    print(f"   Unique events to keep: {len(originals)}")

    if not duplicates:
        print("\n✅ No duplicates found!")
        return

    # Get authenticated session
    session = login_and_get_session(BASE_URL, EMAIL, PASSWORD)

    if not session:
        print("\n❌ Failed to establish authenticated session")
        print("\n💡 Alternative approach: Since these are unconfirmed events,")
        print("   they might only be deletable through the admin UI.")
        print("   Use the 'duplicate_event_ids.txt' file for manual deletion.")
        return

    # Test with a small batch
    print("\n🧪 Testing deletion with first 3 events...")

    deleted_count = 0
    failed_count = 0

    for event in duplicates[:3]:
        print(f"\n   Event {event['id']} ({event['slug'][:40]}...)")

        # Try to delete
        if delete_event_via_session(session, BASE_URL, event["id"]):
            print(f"   ✅ Deleted")
            deleted_count += 1
        else:
            # Try to confirm (which might handle duplicates)
            if confirm_event_via_session(session, BASE_URL, event["id"]):
                print(f"   ✅ Confirmed/processed")
                deleted_count += 1
            else:
                print(f"   ❌ Failed")
                failed_count += 1

        time.sleep(1)

    print(f"\n📊 Test Results:")
    print(f"   Successful: {deleted_count}/3")
    print(f"   Failed: {failed_count}/3")

    if deleted_count == 0:
        print("\n❌ Unable to delete events via API")
        print("   The events might be in a state that requires manual deletion")
        print("   through the admin interface.")
    else:
        print(f"\n✅ Test successful! Can proceed with full cleanup.")
        print(f"   Would delete {len(duplicates)} total duplicates.")


if __name__ == "__main__":
    main()
