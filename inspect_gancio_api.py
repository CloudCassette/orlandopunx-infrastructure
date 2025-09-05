#!/usr/bin/env python3

import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def capture_network_requests():
    """Capture network requests made by the admin interface"""

    # Enable logging
    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"

    print("Starting Chrome browser with network logging...")
    driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)

    try:
        # Login first
        print("Logging in to admin interface...")
        driver.get("https://orlandopunx.com/login")

        # Wait for and fill login form
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
            )
        )
        password_input = driver.find_element(
            By.CSS_SELECTOR, "input[type='password'], input[name='password']"
        )

        email_input.clear()
        email_input.send_keys("admin")
        password_input.clear()
        password_input.send_keys("OrlandoPunkShows2024!")

        # Submit login
        login_button = driver.find_element(
            By.CSS_SELECTOR, "button[type='submit'], .v-btn"
        )
        login_button.click()

        # Wait for redirect
        time.sleep(3)

        # Navigate to admin page
        print("Navigating to admin page...")
        driver.get("https://orlandopunx.com/admin")
        time.sleep(3)

        # Click on Events tab to trigger API calls
        print("Clicking Events tab...")
        events_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'v-tab') and contains(., 'Events')]")
            )
        )
        events_tab.click()
        time.sleep(5)

        # Get network logs
        print("Analyzing network requests...")
        logs = driver.get_log("performance")

        api_requests = []
        for log in logs:
            message = json.loads(log["message"])
            if message["message"]["method"] == "Network.requestWillBeSent":
                url = message["message"]["params"]["request"]["url"]
                method = message["message"]["params"]["request"]["method"]

                if "orlandopunx.com" in url and ("api" in url or "admin" in url):
                    api_requests.append(
                        {
                            "method": method,
                            "url": url,
                            "headers": message["message"]["params"]["request"].get(
                                "headers", {}
                            ),
                        }
                    )

        print(f"\nFound {len(api_requests)} API requests:")
        for req in api_requests:
            print(f"{req['method']} {req['url']}")

        return api_requests

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    capture_network_requests()
