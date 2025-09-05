#!/usr/bin/env python3
"""
Properly navigate to the Events section by finding the clickable parent element
"""

import os
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def navigate_to_events():
    print("🎯 NAVIGATING TO EVENTS SECTION")
    print("=" * 40)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Login
        print("🔑 Logging in...")
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        driver.get("http://localhost:13120/login")
        time.sleep(3)

        email_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

        email_field.send_keys(email)
        password_field.send_keys(password)

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(5)

        # Go to admin
        driver.get("http://localhost:13120/admin")
        time.sleep(5)

        print("🔍 Finding Events badge and its clickable parent...")

        # Find the Events badge
        badge_elements = driver.find_elements(By.CSS_SELECTOR, ".v-badge")
        events_badge = None

        for badge in badge_elements:
            if "events" in badge.text.lower() and "849" in badge.text:
                events_badge = badge
                print(f"✅ Found Events badge: {badge.text.strip()}")
                break

        if events_badge:
            # Find clickable parent elements
            possible_parents = []

            # Check parent elements up the DOM tree
            parent = events_badge
            for i in range(5):  # Check up to 5 levels up
                try:
                    parent = parent.find_element(By.XPATH, "..")
                    tag_name = parent.tag_name
                    classes = parent.get_attribute("class") or ""

                    # Check if this parent is likely clickable
                    if any(
                        clickable in tag_name.lower() for clickable in ["a", "button"]
                    ) or any(
                        clickable in classes.lower()
                        for clickable in [
                            "clickable",
                            "btn",
                            "button",
                            "link",
                            "item",
                            "list-item",
                        ]
                    ):
                        possible_parents.append(parent)
                        print(
                            f"   Found clickable parent {i+1}: {tag_name} with class '{classes}'"
                        )

                except Exception as e:
                    break

            # Also look for siblings that might be clickable
            try:
                siblings = events_badge.find_elements(By.XPATH, "../*")
                for sibling in siblings:
                    tag_name = sibling.tag_name
                    classes = sibling.get_attribute("class") or ""
                    if any(
                        clickable in tag_name.lower() for clickable in ["a", "button"]
                    ):
                        possible_parents.append(sibling)
                        print(
                            f"   Found clickable sibling: {tag_name} with class '{classes}'"
                        )
            except:
                pass

            # Try to click the most promising parent
            clicked = False

            for parent in possible_parents:
                try:
                    print(f"🖱️ Attempting to click parent element...")

                    # Scroll to element first
                    driver.execute_script("arguments[0].scrollIntoView();", parent)
                    time.sleep(1)

                    # Try regular click
                    try:
                        parent.click()
                        clicked = True
                        print("✅ Successfully clicked parent element")
                        break
                    except:
                        # Try JavaScript click
                        driver.execute_script("arguments[0].click();", parent)
                        clicked = True
                        print("✅ Successfully clicked parent element (JS)")
                        break

                except Exception as e:
                    print(f"   ❌ Failed to click parent: {e}")
                    continue

            if not clicked:
                # Try clicking the area around the badge
                print("🖱️ Trying to click near the badge...")
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(events_badge).click().perform()
                    clicked = True
                    print("✅ Successfully clicked via ActionChains")
                except Exception as e:
                    print(f"   ❌ ActionChains failed: {e}")

            if clicked:
                time.sleep(3)
                print(f"📍 After click - URL: {driver.current_url}")
                print(f"📍 After click - Title: {driver.title}")

                # Now look for the events list
                print("\n🔍 SCANNING FOR EVENTS LIST")
                print("-" * 30)

                # Look for table elements (common for admin data)
                tables = driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    print(f"📊 Found {len(tables)} tables")
                    for i, table in enumerate(tables):
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        if len(rows) > 1:
                            print(f"   Table {i+1}: {len(rows)} rows")
                            # Show first few rows
                            for j, row in enumerate(rows[:5]):
                                text = row.text.strip()
                                if text and len(text) > 5:
                                    print(f"     Row {j+1}: {text[:100]}...")

                # Look for list elements
                lists = driver.find_elements(By.CSS_SELECTOR, "ul, ol, .v-list")
                if lists:
                    print(f"📋 Found {len(lists)} list elements")
                    for i, ul in enumerate(lists):
                        items = ul.find_elements(By.CSS_SELECTOR, "li, .v-list-item")
                        if len(items) > 1:
                            print(f"   List {i+1}: {len(items)} items")
                            for j, item in enumerate(items[:3]):
                                text = item.text.strip()
                                if text and len(text) > 5:
                                    print(f"     Item {j+1}: {text[:100]}...")

                # Look for cards or data containers
                containers = driver.find_elements(
                    By.CSS_SELECTOR, ".v-card, .card, .data-table, .v-data-table"
                )
                if containers:
                    print(f"🎴 Found {len(containers)} data containers")
                    for i, container in enumerate(containers[:3]):
                        text = container.text.strip()
                        if text and len(text) > 20:
                            print(f"   Container {i+1}: {text[:150]}...")

                # Check if we can see pagination or "load more"
                pagination_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    ".v-pagination, .pagination, button:contains('more'), button:contains('next')",
                )
                if pagination_elements:
                    print(f"📄 Found {len(pagination_elements)} pagination elements")

                # Save the page source
                with open("/tmp/events_list_page.html", "w") as f:
                    f.write(driver.page_source)
                print("💾 Saved events page source to /tmp/events_list_page.html")

            else:
                print("❌ Could not click to access events")
        else:
            print("❌ Could not find Events badge")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    navigate_to_events()
