#!/usr/bin/env python3

import sys
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def setup_driver(headless=True):
    """Setup Chromium WebDriver"""
    options = Options()
    options.binary_location = "/usr/bin/chromium"

    if headless:
        options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        print("✓ Chromium WebDriver started successfully")
        return driver
    except Exception as e:
        print(f"ERROR: Could not start Chromium WebDriver: {e}")
        sys.exit(1)


def login_and_debug_events():
    """Login and debug the events table loading issue"""
    config = {
        "BASE_URL": "https://orlandopunx.com",
        "EMAIL": "godlessamericarecords@gmail.com",
        "PASSWORD": "Marmalade-Stapling-Watch7",
    }

    driver = setup_driver(headless=True)

    try:
        # Login process (we know this works)
        print("1. Logging in...")
        login_url = f"{config['BASE_URL']}/login"
        driver.get(login_url)
        time.sleep(5)

        # Fill login form
        email_field = driver.find_element(By.ID, "input-45")
        email_field.send_keys(config["EMAIL"])

        password_field = driver.find_element(By.ID, "input-48")
        password_field.send_keys(config["PASSWORD"])

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        time.sleep(8)

        # Navigate to admin page
        print("2. Navigating to admin page...")
        admin_url = f"{config['BASE_URL']}/admin"
        driver.get(admin_url)
        time.sleep(5)

        print("3. Looking for Events element...")
        events_selectors = [
            "//span[contains(text(), 'Events')]",
            "//div[contains(@class, 'v-tab') and contains(., 'Events')]",
            "//div[contains(@class, 'v-badge') and contains(., 'Events')]",
        ]

        events_element = None
        for selector in events_selectors:
            try:
                events_element = driver.find_element(By.XPATH, selector)
                print(f"✓ Found Events element using: {selector}")
                print(f"  Element text: '{events_element.text.strip()}'")
                break
            except:
                print(f"✗ Could not find Events element using: {selector}")
                continue

        if not events_element:
            print("❌ Could not find Events element")
            return

        print("4. Clicking Events element...")
        events_element.click()
        print("✓ Clicked Events element")

        # Wait and observe what happens
        print("5. Waiting and observing page changes...")
        for i in range(1, 11):  # Wait up to 30 seconds, checking every 3 seconds
            print(f"  Checking after {i*3} seconds...")
            time.sleep(3)

            # Look for different types of tables/data containers
            table_selectors = [
                "v-data-table",
                "v-data-table__wrapper",
                "v-simple-table",
                "table",
                "tbody",
            ]

            tables_found = {}
            for selector in table_selectors:
                elements = (
                    driver.find_elements(By.CLASS_NAME, selector)
                    if selector.startswith("v-")
                    else driver.find_elements(By.TAG_NAME, selector)
                )
                if elements:
                    tables_found[selector] = len(elements)

            if tables_found:
                print(f"    Found tables: {tables_found}")

                # Check for actual event data
                rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
                if rows:
                    print(f"    Found {len(rows)} table rows!")

                    # Show first few rows
                    for j, row in enumerate(rows[:3]):
                        cells = row.find_elements(By.XPATH, ".//td")
                        if len(cells) >= 3:
                            title = cells[0].text.strip()[:30]
                            place = cells[1].text.strip()[:20]
                            when = cells[2].text.strip()[:15]
                            print(f"      Row {j}: '{title}' | '{place}' | '{when}'")

                    print("🎉 SUCCESS! Events table loaded with data!")
                    return
                else:
                    print("    Tables found but no data rows yet...")
            else:
                print("    No tables found yet...")

        print("6. Final page inspection...")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Look for any elements that might contain event data
        potential_containers = [
            "//div[contains(@class, 'container')]",
            "//div[contains(@class, 'v-card')]",
            "//div[contains(@class, 'v-window-item')]",
            "//div[contains(@class, 'v-tab-item')]",
        ]

        for selector in potential_containers:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                print(f"Found {len(elements)} elements for: {selector}")
                for elem in elements[:2]:  # Check first 2
                    text = elem.text.strip()[:100]
                    if text:
                        print(f"  Content sample: '{text}...'")

        # Save page source for analysis
        with open("events_page_debug.html", "w") as f:
            f.write(driver.page_source)
        print("💾 Saved page source to events_page_debug.html")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    login_and_debug_events()
