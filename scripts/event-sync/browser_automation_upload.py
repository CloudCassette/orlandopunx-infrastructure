#!/usr/bin/env python3
"""
Browser Automation Approach - Use Selenium to Upload Images
This is the nuclear option that should definitely work
"""

import os
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()


class SeleniumGancioUpload:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"❌ Chrome/Selenium setup failed: {e}")
            print(
                "💡 You might need to install chromedriver: sudo apt install chromium-chromedriver"
            )
            self.driver = None

    def login(self):
        """Login to Gancio"""
        if not self.driver:
            return False

        try:
            email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
            password = os.getenv("GANCIO_PASSWORD")

            print("🌐 Opening login page...")
            self.driver.get(f"{self.gancio_base_url}/login")

            # Wait for and fill email
            email_field = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
                )
            )
            email_field.send_keys(email)

            # Fill password
            password_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password'], input[name='password']"
            )
            password_field.send_keys(password)

            # Submit form
            login_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
            )
            login_button.click()

            # Wait for redirect/success
            time.sleep(3)

            print("✅ Login successful")
            return True

        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def create_event_with_image(self, title, description, image_path):
        """Create an event with image using the web interface"""
        if not self.driver:
            return False

        try:
            print(f"📝 Creating event: {title}")

            # Go to add event page
            self.driver.get(f"{self.gancio_base_url}/add")
            time.sleep(2)

            # Fill title
            title_field = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "input[id*='title'], input[placeholder*='title'], input[aria-label*='title']",
                    )
                )
            )
            title_field.clear()
            title_field.send_keys(title)

            # Fill description (might be a rich text editor)
            try:
                desc_field = self.driver.find_element(
                    By.CSS_SELECTOR, "textarea, div[contenteditable='true'], .editor"
                )
                desc_field.clear()
                desc_field.send_keys(description)
            except:
                print("   ⚠️  Description field not found or not accessible")

            # Select venue (Will's Pub)
            try:
                venue_field = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[id*='place'], select[id*='place'], input[placeholder*='place']",
                )
                venue_field.click()
                time.sleep(1)

                # Look for Will's Pub option
                willspub_option = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'Will')]"
                )
                willspub_option.click()
            except:
                print("   ⚠️  Venue selection not accessible via automation")

            # Set date/time
            try:
                start_time = datetime.now() + timedelta(days=1)

                # Try to find date/time fields
                date_fields = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='date'], input[type='datetime-local'], input[id*='date']",
                )
                for field in date_fields:
                    field.clear()
                    field.send_keys(start_time.strftime("%Y-%m-%d"))

                time_fields = self.driver.find_elements(
                    By.CSS_SELECTOR, "input[type='time'], input[id*='time']"
                )
                for field in time_fields:
                    field.clear()
                    field.send_keys("20:00")
            except:
                print("   ⚠️  Date/time fields not accessible via automation")

            # Upload image - this is the critical part
            try:
                file_input = self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='file']"
                )
                file_input.send_keys(os.path.abspath(image_path))
                print(f"   📷 Image uploaded: {os.path.basename(image_path)}")
                time.sleep(2)  # Wait for upload to process
            except Exception as e:
                print(f"   ❌ Image upload failed: {e}")
                return False

            # Submit the form
            try:
                submit_button = self.wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            "button[type='submit'], input[type='submit'], button:contains('Invia'), button:contains('Submit')",
                        )
                    )
                )
                submit_button.click()

                # Wait for success/redirect
                time.sleep(5)

                print("   ✅ Event submitted successfully")
                return True

            except Exception as e:
                print(f"   ❌ Form submission failed: {e}")
                return False

        except Exception as e:
            print(f"❌ Event creation failed: {e}")
            return False

    def test_browser_upload(self):
        """Test the complete browser automation workflow"""
        if not self.driver:
            return False

        try:
            # Login
            if not self.login():
                return False

            # Find a test image
            flyer_dir = "flyers"
            if not os.path.exists(flyer_dir):
                print("❌ No flyers directory")
                return False

            flyers = [
                f
                for f in os.listdir(flyer_dir)
                if f.endswith(".jpg") and not f.startswith("Buy_Tickets")
            ]
            if not flyers:
                print("❌ No good flyers found")
                return False

            test_image = os.path.join(flyer_dir, flyers[0])

            # Create event
            success = self.create_event_with_image(
                title="SELENIUM TEST - Automated Browser Upload",
                description="Testing browser automation for image upload",
                image_path=test_image,
            )

            return success

        finally:
            if self.driver:
                self.driver.quit()

    def __del__(self):
        if hasattr(self, "driver") and self.driver:
            self.driver.quit()


if __name__ == "__main__":
    uploader = SeleniumGancioUpload()

    if uploader.driver:
        print("🤖 Testing browser automation...")
        success = uploader.test_browser_upload()

        if success:
            print("🎉 Browser automation successful!")

            # Check if event was created
            print("🔍 Checking for created event...")
            import requests

            try:
                resp = requests.get("http://localhost:13120/api/events")
                if resp.status_code == 200:
                    events = resp.json()
                    for event in events:
                        if "SELENIUM TEST" in event.get("title", ""):
                            print(f"✅ Found automated event: {event['title']}")
                            if "media" in event and event["media"]:
                                print(f"   📷 Has image: {event['media'][0]['url']}")
                            else:
                                print("   ❌ No image attached")
                            break
            except Exception as e:
                print(f"Error checking: {e}")
        else:
            print("❌ Browser automation failed")
    else:
        print("❌ Selenium/Chrome not available")
        print("💡 Install with: sudo apt install chromium-chromedriver python3-selenium")
