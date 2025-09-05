#!/usr/bin/env python3
"""
Explore Gancio admin interface to find where events are located
"""

import os
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def explore_admin_interface():
    print("🔧 EXPLORING GANCIO ADMIN INTERFACE")
    print("=" * 50)

    # Setup browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Login first
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

        print("✅ Logged in successfully")

        # Explore different admin pages
        admin_pages = [
            "/admin",
            "/admin/events",
            "/admin/moderation",
            "/admin/pending",
            "/admin/approval",
            "/admin/queue",
            "/user",
            "/profile",
            "/manage",
        ]

        for page in admin_pages:
            try:
                print(f"\n📋 EXPLORING: {page}")
                print("-" * 30)

                driver.get(f"http://localhost:13120{page}")
                time.sleep(3)

                print(f"✅ Page title: {driver.title}")
                print(f"✅ URL: {driver.current_url}")

                # Check for event-related content
                page_source = driver.page_source.lower()
                event_keywords = [
                    "event",
                    "title",
                    "venue",
                    "date",
                    "pending",
                    "approve",
                    "moderation",
                ]
                found_keywords = [kw for kw in event_keywords if kw in page_source]

                if found_keywords:
                    print(f"🎯 Contains keywords: {found_keywords}")

                    # Look for navigation links/tabs
                    nav_links = driver.find_elements(By.TAG_NAME, "a")
                    admin_nav_links = []

                    for link in nav_links:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        if (
                            href
                            and text
                            and any(
                                word in text.lower()
                                for word in [
                                    "event",
                                    "manage",
                                    "admin",
                                    "pending",
                                    "approval",
                                ]
                            )
                        ):
                            admin_nav_links.append((text, href))

                    if admin_nav_links:
                        print("🔗 Found navigation links:")
                        for text, href in admin_nav_links[:5]:
                            print(f"   {text}: {href}")

                    # Count potential event containers
                    containers = []

                    # Table rows
                    rows = driver.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:
                        print(f"📊 Found {len(rows)} table rows")
                        containers.extend(rows)

                        # Show content of first few rows
                        for i, row in enumerate(rows[:3]):
                            text = row.text.strip()
                            if text and len(text) > 5:
                                print(f"   Row {i+1}: {text[:100]}...")

                    # Cards/items
                    cards = driver.find_elements(
                        By.CSS_SELECTOR, ".card, .item, .event, .list-item"
                    )
                    if cards:
                        print(f"🎴 Found {len(cards)} card/item elements")
                        containers.extend(cards)

                        for i, card in enumerate(cards[:3]):
                            text = card.text.strip()
                            if text and len(text) > 5:
                                print(f"   Card {i+1}: {text[:100]}...")

                    # Divs with substantial content
                    divs = driver.find_elements(By.TAG_NAME, "div")
                    content_divs = []
                    for div in divs:
                        text = div.text.strip()
                        if (
                            len(text) > 20 and len(text) < 500
                        ):  # Reasonable content size
                            content_divs.append(div)

                    if content_divs:
                        print(f"📄 Found {len(content_divs)} content divs")
                        for i, div in enumerate(content_divs[:3]):
                            text = div.text.strip()
                            print(f"   Div {i+1}: {text[:100]}...")

                    # Look for pagination or "load more" buttons
                    pagination = driver.find_elements(
                        By.CSS_SELECTOR,
                        ".pagination, .pager, [class*='page'], button:contains('more'), button:contains('next')",
                    )
                    if pagination:
                        print(f"📄 Found pagination elements: {len(pagination)}")

                    # Save page source for manual inspection
                    with open(
                        f"/tmp/gancio_admin_{page.replace('/', '_')}.html", "w"
                    ) as f:
                        f.write(driver.page_source)
                    print(
                        f"💾 Saved page source to /tmp/gancio_admin_{page.replace('/', '_')}.html"
                    )

                else:
                    print("⚠️ No event-related content found")

            except Exception as e:
                print(f"❌ Error exploring {page}: {e}")

        # Check if we need to look for SPA (Single Page App) navigation
        print(f"\n🕸️ CHECKING FOR SPA NAVIGATION")
        print("-" * 40)

        driver.get("http://localhost:13120/admin")
        time.sleep(3)

        # Look for clickable elements that might trigger navigation
        clickable_elements = driver.find_elements(
            By.CSS_SELECTOR, "button, a, [onclick], [role='button']"
        )

        print(f"🖱️ Found {len(clickable_elements)} clickable elements")

        event_related_clickables = []
        for elem in clickable_elements:
            text = elem.text.strip().lower()
            if text and any(
                word in text
                for word in [
                    "event",
                    "manage",
                    "admin",
                    "pending",
                    "approval",
                    "moderation",
                ]
            ):
                event_related_clickables.append((elem.text.strip(), elem.tag_name))

        if event_related_clickables:
            print("🎯 Found event-related clickable elements:")
            for text, tag in event_related_clickables:
                print(f"   {tag}: {text}")

    except Exception as e:
        print(f"❌ Exploration error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    explore_admin_interface()
