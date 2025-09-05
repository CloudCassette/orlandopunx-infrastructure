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


def test_login():
    """Test login to Gancio and inspect the page"""
    config = {
        "BASE_URL": "https://orlandopunx.com",
        "EMAIL": "godlessamericarecords@gmail.com",
        "PASSWORD": "Marmalade-Stapling-Watch7",
    }

    driver = setup_driver(headless=True)

    try:
        # Go to login page
        login_url = f"{config['BASE_URL']}/login"
        print(f"Going to login page: {login_url}")
        driver.get(login_url)

        # Wait a bit for page to load
        time.sleep(5)

        # Print page title and URL
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")

        # Check if we're on the right page
        if "login" not in driver.current_url.lower():
            print("Warning: URL doesn't contain 'login'")

        # Try to find all input elements on the page
        print("Looking for input elements...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input elements:")

        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_id = inp.get_attribute("id")
            input_name = inp.get_attribute("name")
            input_placeholder = inp.get_attribute("placeholder")
            print(
                f"  Input {i}: type='{input_type}', id='{input_id}', name='{input_name}', placeholder='{input_placeholder}'"
            )

        # Try different email field selectors
        email_selectors = [
            "input-45",  # Known from previous attempts
            "input[type='email']",
            "input[name='email']",
            "input[placeholder*='mail' i]",
            "input[placeholder*='Email' i]",
        ]

        email_field = None
        for selector in email_selectors:
            try:
                if selector.startswith("input"):
                    email_field = driver.find_element(By.CSS_SELECTOR, selector)
                else:
                    email_field = driver.find_element(By.ID, selector)
                print(f"✓ Found email field using: {selector}")
                break
            except:
                continue

        if email_field:
            print("Attempting to fill email field...")
            email_field.clear()
            email_field.send_keys(config["EMAIL"])
            print("✓ Email entered")

            # Look for password field
            password_selectors = [
                "input-48",  # Known from previous attempts
                "input[type='password']",
                "input[name='password']",
            ]

            password_field = None
            for selector in password_selectors:
                try:
                    if selector.startswith("input"):
                        password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    else:
                        password_field = driver.find_element(By.ID, selector)
                    print(f"✓ Found password field using: {selector}")
                    break
                except:
                    continue

            if password_field:
                password_field.clear()
                password_field.send_keys(config["PASSWORD"])
                print("✓ Password entered")

                # Look for login button
                button_selectors = [
                    "//button[contains(., 'Login')]",
                    "//button[contains(., 'Sign')]",
                    "//input[@type='submit']",
                    "//button[@type='submit']",
                ]

                login_button = None
                for selector in button_selectors:
                    try:
                        login_button = driver.find_element(By.XPATH, selector)
                        print(f"✓ Found login button using: {selector}")
                        break
                    except:
                        continue

                if login_button:
                    print("Clicking login button...")
                    login_button.click()

                    # Wait a bit and check result
                    time.sleep(5)
                    print(f"After login - URL: {driver.current_url}")
                    print(f"After login - Title: {driver.title}")

                    # Check if we're logged in (look for admin elements)
                    admin_elements = driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'v-badge')]"
                    )
                    if admin_elements:
                        print(
                            f"✓ Found {len(admin_elements)} admin badge elements - login likely successful!"
                        )

                        # Look for event count
                        for elem in admin_elements:
                            text = elem.text
                            if text and any(char.isdigit() for char in text):
                                print(f"Badge text: '{text}'")
                    else:
                        print("✗ No admin badge elements found - login may have failed")
                        # Print page source for debugging (first 1000 chars)
                        source = driver.page_source[:1000]
                        print(f"Page source sample: {source}")
                else:
                    print("✗ Could not find login button")
            else:
                print("✗ Could not find password field")
        else:
            print("✗ Could not find email field")
            print("Page source (first 2000 chars):")
            print(driver.page_source[:2000])

    except Exception as e:
        print(f"Test failed: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_login()
