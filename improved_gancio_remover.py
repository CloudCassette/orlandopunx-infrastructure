#!/usr/bin/env python3

import json
import re
import time
from collections import defaultdict
from urllib.parse import urljoin

import requests


class GancioAPI:
    def __init__(self, base_url, email, password):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def login(self):
        """Login to Gancio admin interface"""
        print(f"Logging in to {self.base_url}...")

        # First get login page to establish session
        login_page = self.session.get(f"{self.base_url}/login")
        if login_page.status_code != 200:
            raise Exception(f"Failed to access login page: {login_page.status_code}")

        # Try form-based login with proper headers
        login_data = {"email": self.email, "password": self.password}

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{self.base_url}/login",
            "Origin": self.base_url,
        }

        login_response = self.session.post(
            f"{self.base_url}/login",
            data=login_data,
            headers=headers,
            allow_redirects=True,
        )

        print(f"Login response status: {login_response.status_code}")
        print(f"Final URL after login: {login_response.url}")

        # Check if we were redirected away from login (success indicator)
        if "/login" not in login_response.url:
            print("✅ Login successful - redirected away from login page")
            return True

        # Alternative: Check admin page access
        admin_response = self.session.get(f"{self.base_url}/admin")
        print(f"Admin page test: {admin_response.status_code}")

        # Look for admin-specific content
        admin_indicators = ["Events", "Users", "Places", "unconfirmedEvents", "Options"]
        admin_content = admin_response.text

        found_indicators = [
            indicator for indicator in admin_indicators if indicator in admin_content
        ]
        print(f"Found admin indicators: {found_indicators}")

        if len(found_indicators) >= 2:
            print("✅ Login successful - admin content detected")
            return True

        print("❌ Login failed - no admin access detected")
        return False

    def get_unconfirmed_events(self):
        """Fetch unconfirmed events from admin interface"""
        print("Fetching unconfirmed events...")

        # Get admin page which should contain the events data
        admin_response = self.session.get(f"{self.base_url}/admin")

        if admin_response.status_code != 200:
            print(f"❌ Failed to access admin page: {admin_response.status_code}")
            return []

        # Parse events from the page HTML (which includes __NUXT__ data)
        events = self.parse_events_from_html(admin_response.text)

        if not events:
            print("Trying to load events dynamically...")
            # The admin page might load events via AJAX, let's try some API endpoints
            api_endpoints = [
                "/api/admin/events",
                "/api/events?unconfirmed=true",
                "/admin/api/events",
                "/nuxt/admin/events",
            ]

            for endpoint in api_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    print(f"Trying {endpoint}: {response.status_code}")

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f"✅ Found {len(data)} events via {endpoint}")
                                return data
                            elif isinstance(data, dict) and "unconfirmedEvents" in data:
                                print(
                                    f"✅ Found events in data structure via {endpoint}"
                                )
                                return data["unconfirmedEvents"]
                        except json.JSONDecodeError:
                            pass
                except Exception as e:
                    print(f"Error with {endpoint}: {e}")

        return events

    def parse_events_from_html(self, html_content):
        """Parse events from HTML page containing __NUXT__ data"""
        events = []

        # Check if we have the same unconfirmed events data as our browser analysis
        if "unconfirmedEvents" in html_content:
            print("✅ Found unconfirmedEvents in HTML")

            # Use the same regex pattern that worked before
            pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
            matches = re.findall(pattern, html_content)

            for match in matches:
                event_id, title_var, slug = match
                events.append(
                    {"id": int(event_id), "title_var": title_var, "slug": slug}
                )

            print(f"Parsed {len(events)} events from HTML")
        else:
            print("No unconfirmedEvents found in HTML")

        # Fallback: use our pre-analyzed data from the saved file
        if not events:
            print("Trying to use saved analysis data...")
            try:
                with open("admin_after_click.html", "r") as f:
                    saved_content = f.read()

                pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
                matches = re.findall(pattern, saved_content)

                for match in matches:
                    event_id, title_var, slug = match
                    events.append(
                        {"id": int(event_id), "title_var": title_var, "slug": slug}
                    )

                print(f"✅ Loaded {len(events)} events from saved file")
            except FileNotFoundError:
                print("No saved event data found")

        return events

    def delete_event(self, event_id):
        """Delete an event by ID"""
        print(f"Attempting to delete event {event_id}...")

        # Get CSRF token first (might be needed)
        admin_page = self.session.get(f"{self.base_url}/admin")
        csrf_token = None

        csrf_match = re.search(
            r'name=["\']_token["\'] value=["\']([^"\']+)["\']', admin_page.text
        )
        if csrf_match:
            csrf_token = csrf_match.group(1)

        # Try different delete endpoints and methods
        delete_attempts = [
            # Standard REST API patterns
            {"method": "DELETE", "url": f"/api/events/{event_id}"},
            {"method": "DELETE", "url": f"/api/admin/events/{event_id}"},
            # Admin interface patterns
            {"method": "POST", "url": f"/admin/events/{event_id}/delete"},
            {
                "method": "POST",
                "url": f"/admin/events/{event_id}",
                "data": {"_method": "DELETE"},
            },
            # Form-based deletion
            {
                "method": "POST",
                "url": f"/admin/events/delete",
                "data": {"id": event_id},
            },
        ]

        for attempt in delete_attempts:
            try:
                url = f"{self.base_url}{attempt['url']}"
                method = attempt["method"]
                data = attempt.get("data", {})

                # Add CSRF token if we have one
                if csrf_token:
                    data["_token"] = csrf_token

                headers = {
                    "Referer": f"{self.base_url}/admin",
                    "X-Requested-With": "XMLHttpRequest",
                }

                if method == "DELETE":
                    response = self.session.delete(url, headers=headers)
                else:
                    response = self.session.post(url, data=data, headers=headers)

                print(f"  {method} {attempt['url']}: {response.status_code}")

                # Success indicators
                if response.status_code in [200, 204, 302]:
                    return True
                elif response.status_code == 404 and "event" in response.text.lower():
                    # Event might already be deleted
                    return True

            except Exception as e:
                print(f"  Error with {attempt}: {e}")

        return False


def analyze_duplicates(events):
    """Analyze events for duplicates based on slug patterns"""
    base_slug_groups = defaultdict(list)

    for event in events:
        base_slug = re.sub(r"-\d+$", "", event["slug"])
        base_slug_groups[base_slug].append(event)

    # Find duplicates - keep the first one, mark others for deletion
    duplicates_to_delete = []
    kept_originals = []

    for base_slug, event_list in base_slug_groups.items():
        if len(event_list) > 1:
            # Sort by ID to keep the earliest one
            event_list.sort(key=lambda x: x["id"])
            kept_originals.append(event_list[0])
            duplicates_to_delete.extend(event_list[1:])  # All but the first
        else:
            kept_originals.append(event_list[0])

    return duplicates_to_delete, kept_originals


def main():
    # Configuration
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"

    # Modes
    DRY_RUN = True  # Set to False to actually delete events
    BATCH_SIZE = 5  # Number of events to delete in each batch (reduced for safety)
    DELAY_BETWEEN_DELETES = (
        3  # Seconds to wait between deletions (increased for safety)
    )

    try:
        # Initialize API client
        api = GancioAPI(BASE_URL, EMAIL, PASSWORD)

        # Login
        if not api.login():
            print("❌ Failed to login. Check credentials.")
            return

        print("✅ Successfully logged in")

        # Get events
        events = api.get_unconfirmed_events()
        if not events:
            print("❌ Could not fetch events")
            return

        print(f"📊 Found {len(events)} total events")

        # Analyze duplicates
        duplicates_to_delete, kept_originals = analyze_duplicates(events)

        print(f"\n📈 Analysis Results:")
        print(f"   Total events: {len(events)}")
        print(f"   Unique events to keep: {len(kept_originals)}")
        print(f"   Duplicate events to delete: {len(duplicates_to_delete)}")

        if not duplicates_to_delete:
            print("✅ No duplicates found!")
            return

        # Show sample of what will be deleted
        print(f"\n🗑️  Sample of events that will be deleted:")
        for i, event in enumerate(duplicates_to_delete[:10]):
            print(f"   {i+1}. ID: {event['id']}, Slug: {event['slug']}")
        if len(duplicates_to_delete) > 10:
            print(f"   ... and {len(duplicates_to_delete) - 10} more")

        # Show sample of what will be kept
        print(f"\n💾 Sample of events that will be kept:")
        for i, event in enumerate(kept_originals[:5]):
            base_slug = re.sub(r"-\d+$", "", event["slug"])
            duplicates_count = len(
                [
                    d
                    for d in duplicates_to_delete
                    if re.sub(r"-\d+$", "", d["slug"]) == base_slug
                ]
            )
            if duplicates_count > 0:
                print(
                    f"   {i+1}. ID: {event['id']}, Slug: {event['slug']} (keeping, deleting {duplicates_count} duplicates)"
                )

        # Confirmation
        if DRY_RUN:
            print(f"\n🔍 DRY RUN MODE - No events will actually be deleted")
            print(f"   To perform actual deletions, set DRY_RUN = False in the script")
            print(f"   and run the script again.")

            # Ask if user wants to proceed with actual deletion
            response = input(
                "\nWould you like to proceed with actual deletions now? (type 'YES' to continue): "
            )
            if response == "YES":
                print(
                    "⚠️  Switching to LIVE MODE - Events will be permanently deleted!"
                )
                time.sleep(2)
                DRY_RUN = False
            else:
                print("✅ Staying in dry-run mode")
                return
        else:
            print(
                f"\n⚠️  WARNING: This will permanently delete {len(duplicates_to_delete)} events!"
            )
            response = input(
                "Are you absolutely sure you want to continue? (type 'DELETE' to confirm): "
            )
            if response != "DELETE":
                print("❌ Cancelled by user")
                return

        if not DRY_RUN:
            # Delete duplicates in batches
            deleted_count = 0
            failed_count = 0

            print(
                f"\n🚀 Starting deletion of {len(duplicates_to_delete)} duplicate events..."
            )
            print(
                f"   Processing in batches of {BATCH_SIZE} with {DELAY_BETWEEN_DELETES}s delays..."
            )

            for i, event in enumerate(duplicates_to_delete):
                print(f"\n[{i+1}/{len(duplicates_to_delete)}] ", end="")

                if api.delete_event(event["id"]):
                    deleted_count += 1
                    print(f"✅ Deleted event {event['id']} ({event['slug']})")
                else:
                    failed_count += 1
                    print(f"❌ Failed to delete event {event['id']} ({event['slug']})")

                # Add delay between deletions
                if (i + 1) % BATCH_SIZE == 0:
                    print(
                        f"   💤 Batch complete, sleeping {DELAY_BETWEEN_DELETES} seconds..."
                    )
                    time.sleep(DELAY_BETWEEN_DELETES)
                else:
                    time.sleep(1)  # Short delay between individual deletions

            # Final results
            print(f"\n📊 Cleanup Results:")
            print(f"   Successfully deleted: {deleted_count}")
            print(f"   Failed to delete: {failed_count}")
            print(f"   Remaining events: {len(kept_originals) + failed_count}")

            if deleted_count > 0:
                print(f"✅ Cleanup completed! Removed {deleted_count} duplicate events.")
                print(
                    f"   Your event calendar should now show {len(kept_originals) + failed_count} events instead of {len(events)}."
                )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
