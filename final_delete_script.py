#!/usr/bin/env python3

import re
import time
from collections import defaultdict

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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


def get_session_cookies():
    """Get authenticated session using Selenium"""
    print("🔐 Getting authenticated session...")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Login
        driver.get("https://orlandopunx.com/login")
        time.sleep(2)

        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.send_keys("admin")

        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.send_keys("OrlandoPunkShows2024!")

        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "login" in btn.text.lower():
                btn.click()
                break

        time.sleep(3)

        # Get cookies
        cookies = driver.get_cookies()
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

        print("✅ Got session cookies")
        return cookie_dict

    finally:
        driver.quit()


def delete_events_via_api(duplicates, cookies):
    """Try to delete events using API endpoints"""

    session = requests.Session()

    # Set cookies
    for name, value in cookies.items():
        session.cookies.set(name, value)

    # Set headers
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
    )

    deleted_count = 0
    failed_count = 0

    # Try different API endpoints
    endpoints = [
        "https://orlandopunx.com/api/event/{}",
        "https://orlandopunx.com/api/events/{}",
        "https://orlandopunx.com/admin/event/{}",
        "https://orlandopunx.com/api/event/{}/delete",
    ]

    for i, event in enumerate(duplicates[:5], 1):  # Test with first 5
        print(
            f"\n[{i}/5] Attempting to delete event {event['id']} ({event['slug'][:50]}...)"
        )

        deleted = False
        for endpoint in endpoints:
            try:
                url = endpoint.format(event["id"])

                # Try DELETE method
                resp = session.delete(url, timeout=5)
                if resp.status_code in [200, 204, 202]:
                    print(f"  ✅ Deleted via DELETE {endpoint}")
                    deleted = True
                    deleted_count += 1
                    break

                # Try POST with delete action
                resp = session.post(url, json={"action": "delete"}, timeout=5)
                if resp.status_code in [200, 204, 202]:
                    print(f"  ✅ Deleted via POST {endpoint}")
                    deleted = True
                    deleted_count += 1
                    break

            except:
                continue

        if not deleted:
            print(f"  ❌ Could not delete event {event['id']}")
            failed_count += 1

        time.sleep(2)  # Don't overwhelm the server

    return deleted_count, failed_count


def main():
    print("🚀 Orlando Punx Duplicate Event Cleanup")
    print("=" * 50)

    # Analyze duplicates
    duplicates, originals = analyze_duplicates_from_saved()

    print(f"\n📊 Found {len(duplicates)} duplicate events to delete")
    print(f"   Keeping {len(originals)} original events")

    if not duplicates:
        print("✅ No duplicates found!")
        return

    # Get authenticated session
    cookies = get_session_cookies()

    # Try to delete via API
    print("\n🗑️  Attempting to delete duplicates via API...")
    deleted, failed = delete_events_via_api(duplicates, cookies)

    print(f"\n📈 Results:")
    print(f"   ✅ Deleted: {deleted}")
    print(f"   ❌ Failed: {failed}")

    if deleted > 0:
        print(f"\n🎉 Successfully deleted {deleted} events!")
        print(f"   {len(duplicates) - deleted} duplicates remain.")
    else:
        print("\n⚠️  API deletion didn't work. Manual deletion may be required.")
        print("   The events admin interface structure may need further analysis.")


if __name__ == "__main__":
    main()
