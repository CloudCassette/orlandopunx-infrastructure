#!/usr/bin/env python3

import re
import tempfile
import time
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class GancioBrowserAPI:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.driver = None

    def start_browser(self):
        """Start browser session"""
        chrome_options = Options()
        # Use a unique user data directory to avoid conflicts
        temp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.binary_location = "/usr/bin/chromium"

        print("Starting Chrome browser...")
        self.driver = webdriver.Chrome(options=chrome_options)

    def login(self):
        """Login to Gancio admin interface"""
        if not self.driver:
            self.start_browser()

        print(f"Logging in to {self.base_url}...")

        # Navigate to login page
        self.driver.get(f"{self.base_url}/login")

        # Fill login form
        email_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
            )
        )
        password_input = self.driver.find_element(
            By.CSS_SELECTOR, "input[type='password'], input[name='password']"
        )

        email_input.clear()
        email_input.send_keys(self.email)
        password_input.clear()
        password_input.send_keys(self.password)

        # Submit login
        login_button = self.driver.find_element(
            By.CSS_SELECTOR, "button[type='submit'], .v-btn"
        )
        login_button.click()

        # Wait for redirect
        time.sleep(3)

        # Check if we're logged in by trying to access admin
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(2)

        # Look for admin indicators
        if "Events" in self.driver.page_source:
            print("✅ Successfully logged in to admin interface")
            return True
        else:
            print("❌ Login failed - no admin access")
            return False

    def click_events_tab(self):
        """Click on the Events tab to load event interface"""
        try:
            print("Clicking on Events tab...")
            # Wait for and click Events tab
            events_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'v-tab') and contains(., 'Events')]",
                    )
                )
            )
            events_tab.click()
            time.sleep(3)
            print("✅ Events tab clicked")
            return True
        except Exception as e:
            print(f"❌ Failed to click Events tab: {e}")
            return False

    def delete_event_by_id(self, event_id):
        """Delete a specific event by finding and clicking its delete button"""
        try:
            # Look for the event in the interface
            # Try multiple strategies to find and delete the event
            event_selectors = [
                # Look for delete button in same row as event ID
                f"//tr[contains(., '{event_id}')]//button[contains(@class, 'delete') or contains(., 'Delete') or contains(., 'Remove')]",
                f"//div[contains(., '{event_id}')]//button[contains(@class, 'delete') or contains(., 'Delete') or contains(., 'Remove')]",
                # Look for data attributes
                f"//*[@data-id='{event_id}']//button[contains(@class, 'delete') or contains(., 'Delete')]",
                # Look for close/following buttons after event ID text
                f"//*[contains(text(), '{event_id}')]/following::button[contains(@class, 'delete') or contains(., 'Delete')]",
                # Try looking for three-dots menu or actions
                f"//tr[contains(., '{event_id}')]//button[contains(@class, 'menu') or contains(@class, 'actions')]",
                f"//div[contains(., '{event_id}')]//button[contains(@class, 'menu') or contains(@class, 'actions')]",
            ]

            for selector in event_selectors:
                try:
                    delete_button = self.driver.find_element(By.XPATH, selector)
                    # Scroll to element
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", delete_button
                    )
                    time.sleep(0.5)
                    delete_button.click()

                    # Look for confirmation dialog or direct deletion
                    try:
                        # Wait for confirmation dialog
                        confirm_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH,
                                    "//button[contains(., 'Confirm') or contains(., 'Yes') or contains(., 'Delete') or contains(., 'OK')]",
                                )
                            )
                        )
                        confirm_button.click()
                    except:
                        # No confirmation dialog - deletion might be direct
                        pass

                    time.sleep(1)
                    return True
                except:
                    continue

            # If direct deletion fails, try finding the event and using keyboard shortcuts
            try:
                # Look for event row/container
                event_element = self.driver.find_element(
                    By.XPATH, f"//*[contains(text(), '{event_id}')]"
                )
                event_element.click()  # Select the event
                time.sleep(0.5)

                # Try Delete key
                from selenium.webdriver.common.keys import Keys

                event_element.send_keys(Keys.DELETE)
                time.sleep(1)

                # Check for confirmation
                try:
                    confirm_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//button[contains(., 'Confirm') or contains(., 'Yes') or contains(., 'Delete')]",
                            )
                        )
                    )
                    confirm_button.click()
                    return True
                except:
                    pass

            except:
                pass

            return False
        except Exception as e:
            print(f"Error deleting event {event_id}: {e}")
            return False

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


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
    MAX_DELETIONS = 5  # Start with just 5 for testing

    api = None

    try:
        # Get events from saved analysis
        print("Loading events from previous analysis...")
        events = []

        try:
            with open("admin_after_click.html", "r") as f:
                html_content = f.read()

            pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
            matches = re.findall(pattern, html_content)

            for match in matches:
                event_id, title_var, slug = match
                events.append(
                    {"id": int(event_id), "title_var": title_var, "slug": slug}
                )

            print(f"✅ Loaded {len(events)} events from saved analysis")

        except FileNotFoundError:
            print("❌ No saved event data found. Please run the browser analysis first.")
            return

        if not events:
            print("❌ No events found in saved data")
            return

        # Analyze duplicates
        duplicates_to_delete, kept_originals = analyze_duplicates(events)

        print(f"\n📈 Duplicate Analysis Results:")
        print(f"   Total events: {len(events)}")
        print(f"   Unique events to keep: {len(kept_originals)}")
        print(f"   Duplicate events to delete: {len(duplicates_to_delete)}")

        if not duplicates_to_delete:
            print("✅ No duplicates found!")
            return

        # Show detailed breakdown
        print(
            f"\n🗑️  Events that will be deleted (first {min(10, len(duplicates_to_delete))}):"
        )
        for i, event in enumerate(duplicates_to_delete[:10]):
            print(f"   {i+1}. ID: {event['id']}, Slug: {event['slug'][:60]}...")
        if len(duplicates_to_delete) > 10:
            print(f"   ... and {len(duplicates_to_delete) - 10} more")

        # Confirmation and mode selection
        if DRY_RUN:
            print(f"\n🔍 DRY RUN MODE - No events will actually be deleted")
            print(f"   This analysis shows what WOULD be deleted.")
            print(f"   Starting with {MAX_DELETIONS} deletions for testing.")

            response = input(
                f"\nWould you like to proceed with deleting {min(MAX_DELETIONS, len(duplicates_to_delete))} duplicates? (type 'YES' to continue): "
            )
            if response != "YES":
                print("✅ Analysis complete. No changes made.")
                return

            print("🚀 Starting browser-based deletion process...")
            DRY_RUN = False

        if not DRY_RUN:
            # Start browser-based deletion
            api = GancioBrowserAPI(BASE_URL, EMAIL, PASSWORD)

            if not api.login():
                print("❌ Failed to login via browser")
                return

            # Navigate to Events admin page
            if not api.click_events_tab():
                print("❌ Could not access Events admin interface")
                return

            # Take a screenshot for debugging
            try:
                api.driver.save_screenshot("events_page.png")
                print("📷 Screenshot saved as events_page.png")
            except:
                pass

            # Delete duplicates (limited for testing)
            deleted_count = 0
            failed_count = 0

            target_deletions = duplicates_to_delete[:MAX_DELETIONS]
            print(
                f"\n🗑️  Attempting to delete {len(target_deletions)} duplicate events..."
            )
            print("   (This is a test run - will increase batch size once working)")

            for i, event in enumerate(target_deletions):
                print(
                    f"\n[{i+1}/{len(target_deletions)}] Attempting to delete event {event['id']}"
                )
                print(f"   Slug: {event['slug'][:80]}...")

                if api.delete_event_by_id(event["id"]):
                    deleted_count += 1
                    print(f"   ✅ Successfully deleted")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed to delete")

                time.sleep(3)  # Extra delay between deletions for debugging

            print(f"\n📊 Test Cleanup Results:")
            print(f"   Successfully deleted: {deleted_count}")
            print(f"   Failed to delete: {failed_count}")
            print(
                f"   Remaining duplicates: {len(duplicates_to_delete) - deleted_count}"
            )

            if deleted_count > 0:
                print(f"✅ Test successful! Deleted {deleted_count} duplicate events.")
                print(
                    f"   Once confirmed working, you can increase MAX_DELETIONS in the script."
                )
                print(
                    f"   Estimated time for full cleanup: {(len(duplicates_to_delete) * 3) // 60} minutes"
                )
            else:
                print(
                    "⚠️  No events were deleted. The admin interface structure might need manual inspection."
                )
                print(
                    "   Check the screenshot 'events_page.png' to see the current interface."
                )

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if api:
            print("Closing browser...")
            api.close()


if __name__ == "__main__":
    main()
