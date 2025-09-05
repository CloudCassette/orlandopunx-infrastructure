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


def authenticate_api(base_url, email, password):
    """Authenticate with Gancio API and get JWT token"""

    print("🔐 Authenticating with Gancio API...")

    # According to docs, login endpoint is POST /api/auth/local
    login_url = f"{base_url}/api/auth/local"

    payload = {"email": email, "password": password}

    try:
        response = requests.post(login_url, json=payload)

        if response.status_code == 200:
            data = response.json()
            # The response should contain a JWT token
            if "token" in data:
                print("✅ Authentication successful")
                return data["token"]
            elif "jwt" in data:
                print("✅ Authentication successful")
                return data["jwt"]
            else:
                # Try to extract token from response
                print(f"Response data: {data}")
                return None
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def delete_event_via_api(base_url, event_id, token):
    """Delete a single event via Gancio API"""

    # According to Gancio API docs, delete endpoint is DELETE /api/event/:id
    delete_url = f"{base_url}/api/event/{event_id}"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.delete(delete_url, headers=headers)

        if response.status_code in [200, 204, 202]:
            return True
        else:
            # Try alternative endpoint for unconfirmed events
            if response.status_code == 404:
                # Maybe it's an unconfirmed event
                delete_url = f"{base_url}/api/event/unconfirmed/{event_id}"
                response = requests.delete(delete_url, headers=headers)
                if response.status_code in [200, 204, 202]:
                    return True
            return False

    except Exception as e:
        print(f"    Error: {e}")
        return False


def delete_duplicates(base_url, duplicates, token, batch_size=10):
    """Delete duplicate events in batches"""

    deleted_count = 0
    failed_count = 0
    failed_ids = []

    print(f"\n🗑️  Deleting {len(duplicates)} duplicate events...")
    print(f"   Processing in batches of {batch_size}...")

    for i in range(0, len(duplicates), batch_size):
        batch = duplicates[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(duplicates) + batch_size - 1) // batch_size

        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} events)")

        for event in batch:
            print(f"   Deleting event {event['id']} ({event['slug'][:40]}...)", end="")

            if delete_event_via_api(base_url, event["id"], token):
                deleted_count += 1
                print(" ✅")
            else:
                failed_count += 1
                failed_ids.append(event["id"])
                print(" ❌")

            # Small delay to not overwhelm the server
            time.sleep(0.5)

        if i + batch_size < len(duplicates):
            print(f"   ⏸️  Pausing between batches...")
            time.sleep(2)

    return deleted_count, failed_count, failed_ids


def main():
    # Configuration
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"

    print("🚀 Orlando Punx Duplicate Event Cleanup (Gancio API)")
    print("=" * 60)

    # Analyze duplicates
    duplicates, originals = analyze_duplicates_from_saved()

    print(f"\n📊 Analysis Results:")
    print(f"   Total events found: {len(duplicates) + len(originals)}")
    print(f"   Duplicate events: {len(duplicates)}")
    print(f"   Unique events to keep: {len(originals)}")

    if not duplicates:
        print("\n✅ No duplicates found! Your calendar is clean.")
        return

    # Show what will be deleted
    print(f"\n📋 Sample of events to be deleted (first 5):")
    for i, event in enumerate(duplicates[:5], 1):
        print(f"   {i}. ID: {event['id']} - {event['slug'][:60]}...")
    if len(duplicates) > 5:
        print(f"   ... and {len(duplicates) - 5} more")

    # Get confirmation
    print(f"\n⚠️  WARNING: This will permanently delete {len(duplicates)} events!")
    print("   Make sure you have a backup if needed.")

    response = input("\n❓ Proceed with deletion? Type 'DELETE' to confirm: ")
    if response != "DELETE":
        print("✅ Operation cancelled. No events were deleted.")
        return

    # Authenticate
    token = authenticate_api(BASE_URL, EMAIL, PASSWORD)

    if not token:
        print("\n❌ Failed to authenticate with API")
        print("   Please check your credentials and try again")
        return

    # Start deletion with small test batch first
    print("\n🧪 Testing with first 3 events...")
    test_batch = duplicates[:3]
    test_deleted, test_failed, _ = delete_duplicates(
        BASE_URL, test_batch, token, batch_size=3
    )

    if test_deleted == 0:
        print("\n❌ Test deletion failed. API might not be accessible.")
        print("   Please check:")
        print("   1. The events are unconfirmed/pending (API might only delete those)")
        print("   2. Your admin account has proper permissions")
        print("   3. The API endpoints are enabled on your instance")
        return

    print(f"\n✅ Test successful! Deleted {test_deleted}/{len(test_batch)} events")

    if len(duplicates) > 3:
        remaining = duplicates[3:]
        print(f"\n📋 {len(remaining)} duplicates remaining")

        response = input("Continue with full deletion? Type 'YES' to proceed: ")
        if response != "YES":
            print("✅ Stopped after test. 3 duplicates deleted.")
            return

        # Delete the rest
        deleted, failed, failed_ids = delete_duplicates(
            BASE_URL, remaining, token, batch_size=20
        )

        total_deleted = test_deleted + deleted
        total_failed = test_failed + failed
    else:
        total_deleted = test_deleted
        total_failed = test_failed
        failed_ids = []

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"✅ Successfully deleted: {total_deleted} events")
    print(f"❌ Failed to delete: {total_failed} events")
    print(f"📈 Events remaining: {len(originals)} (unique events kept)")

    if total_deleted > 0:
        reduction_percent = (total_deleted / (len(duplicates) + len(originals))) * 100
        print(f"\n🎉 SUCCESS! Your calendar is now {reduction_percent:.1f}% smaller!")
        print(f"   Cleaned up {total_deleted} duplicate events.")

    if failed_ids:
        print(f"\n⚠️  Failed event IDs (you may need to delete manually):")
        print(f"   {','.join(map(str, failed_ids[:20]))}")
        if len(failed_ids) > 20:
            print(f"   ... and {len(failed_ids) - 20} more")


if __name__ == "__main__":
    main()
