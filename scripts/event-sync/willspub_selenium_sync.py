#!/usr/bin/env python3
"""
Will's Pub to Gancio Sync using Selenium (Browser Automation)
This works with SPAs that require JavaScript execution
"""

import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Check if selenium is available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class SeleniumGancioSync:
    def __init__(self, gancio_base_url):
        self.willspub_url = "https://willspub.org"
        self.gancio_base_url = gancio_base_url.rstrip("/")

        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not available. Install with:")
            print("   pip install selenium")
            print("   And install ChromeDriver")
            return

        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        # Remove headless for debugging - you can add it back later
        # self.chrome_options.add_argument('--headless')

        self.driver = None

        # Known place mappings
        self.places = {
            "Will's Pub": "Will's Pub",
            "Uncle Lou's": "Uncle Lou's",
            "Lil' Indies": "Will's Pub",  # Assume same as Will's Pub
        }

    def scrape_events_simple(self, limit=3):
        """Simple event scraping without browser automation"""
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

        try:
            print(f"📥 Scraping events from Will's Pub...")
            response = session.get(self.willspub_url, timeout=30)
            response.raise_for_status()

            content = response.text

            # Extract events from JavaScript
            events = []
            lines = content.split("\n")

            for line in lines:
                if "EventData.events.push" in line and '"type" : "event"' in line:
                    try:
                        display_match = re.search(r'"display" : "([^"]+)"', line)
                        url_match = re.search(r'"url" : "([^"]+)"', line)

                        if all([display_match, url_match]):
                            display = (
                                display_match.group(1)
                                .replace("&amp;", "&")
                                .replace("&#039;", "'")
                            )

                            # Parse title and date
                            date_match = re.search(r"(\d{2}/\d{2})$", display)
                            if date_match:
                                title = display[:-6].strip()
                            else:
                                title = display

                            events.append({"title": title, "url": url_match.group(1)})

                            if limit and len(events) >= limit:
                                break

                    except Exception:
                        continue

            # Get details for each event (simplified)
            detailed_events = []
            for i, event in enumerate(events, 1):
                print(f"📋 [{i}/{len(events)}] {event['title']}")

                try:
                    event_resp = session.get(event["url"], timeout=15)
                    soup = BeautifulSoup(event_resp.content, "html.parser")

                    details = {
                        "title": event["title"],
                        "source_url": event["url"],
                        "venue": "Will's Pub",
                    }

                    # Extract date
                    date_elem = soup.find("span", class_="tw-event-date")
                    if date_elem:
                        date_str = date_elem.text.strip()
                        details["date_string"] = date_str
                        details["parsed_date"] = self.parse_date(date_str)

                    # Extract time
                    time_elem = soup.find("span", class_="tw-event-door-time")
                    if time_elem:
                        time_str = time_elem.text.strip()
                        details["parsed_time"] = self.parse_time(time_str)
                    else:
                        details["parsed_time"] = "19:00"

                    # Extract description
                    desc_elem = soup.find("div", class_="event-description")
                    if desc_elem:
                        details["description"] = desc_elem.get_text().strip()[:300]
                    else:
                        details["description"] = f"Event at {details['venue']}"

                    detailed_events.append(details)
                    time.sleep(0.5)

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue

            return detailed_events

        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []

    def parse_date(self, date_str):
        """Parse date string"""
        try:
            date_str = re.sub(r"\s+", " ", date_str.strip())

            formats = [
                "%b %d, %Y",  # Aug 10, 2025
                "%a %b, %d %Y",  # Sun Aug, 10 2025
                "%a %b %d, %Y",  # Sun Aug 10, 2025
            ]

            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            return None
        except Exception:
            return None

    def parse_time(self, time_str):
        """Parse time string"""
        try:
            time_match = re.search(r"(\d{1,2}):(\d{2})\s*([AP]M)", time_str, re.I)
            if time_match:
                hour, minute, ampm = time_match.groups()
                hour = int(hour)
                minute = int(minute)

                if ampm.upper() == "PM" and hour != 12:
                    hour += 12
                elif ampm.upper() == "AM" and hour == 12:
                    hour = 0

                return f"{hour:02d}:{minute:02d}"

            return "19:00"
        except Exception:
            return "19:00"

    def start_browser(self):
        """Start the browser"""
        if not SELENIUM_AVAILABLE:
            return False

        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            return True
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            print("   Make sure ChromeDriver is installed and in PATH")
            return False

    def login_to_gancio(self):
        """Login to Gancio via browser"""
        if not self.driver:
            return False

        try:
            print("🔑 Logging into Gancio...")
            self.driver.get(f"{self.gancio_base_url}/login")

            # Wait for login form
            wait = WebDriverWait(self.driver, 10)

            email = input("Enter your Gancio email: ").strip()
            password = input("Enter your Gancio password: ").strip()

            # Fill login form
            email_field = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
                )
            )
            password_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password'], input[name='password']"
            )

            email_field.send_keys(email)
            password_field.send_keys(password)

            # Submit form
            submit_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
            )
            submit_button.click()

            # Wait for redirect
            time.sleep(3)

            if "/login" not in self.driver.current_url:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def create_event_in_browser(self, event_data):
        """Create event using browser automation"""
        if not self.driver:
            return False

        try:
            print(f"   🌐 Creating: {event_data.get('title', 'Unknown')}")

            # Go to add event page
            self.driver.get(f"{self.gancio_base_url}/add")

            # Wait for form to load
            wait = WebDriverWait(self.driver, 10)

            # Fill title
            title_field = wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "input[name='title'], #title, [placeholder*='title'], [placeholder*='nome']",
                    )
                )
            )
            title_field.clear()
            title_field.send_keys(event_data.get("title", ""))

            # Fill description
            try:
                desc_field = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "textarea[name='description'], #description, [placeholder*='description']",
                )
                desc_field.clear()
                desc_field.send_keys(event_data.get("description", ""))
            except:
                print("   ⚠️  Description field not found")

            # Set date
            if event_data.get("parsed_date"):
                try:
                    date_field = self.driver.find_element(
                        By.CSS_SELECTOR, "input[type='date'], input[name='date']"
                    )
                    date_field.clear()
                    date_field.send_keys(event_data["parsed_date"])
                except:
                    print("   ⚠️  Date field not found")

            # Set time
            if event_data.get("parsed_time"):
                try:
                    time_field = self.driver.find_element(
                        By.CSS_SELECTOR, "input[type='time'], input[name='time']"
                    )
                    time_field.clear()
                    time_field.send_keys(event_data["parsed_time"])
                except:
                    print("   ⚠️  Time field not found")

            # Select venue/place
            try:
                venue_select = self.driver.find_element(
                    By.CSS_SELECTOR, "select[name='place'], select[name='placeId']"
                )
                for option in venue_select.find_elements(By.TAG_NAME, "option"):
                    if event_data.get("venue", "Will's Pub") in option.text:
                        option.click()
                        break
            except:
                print("   ⚠️  Venue selector not found")

            print("   ⏸️  Form filled - MANUAL SUBMISSION REQUIRED")
            print("   👀 Please review the form and submit manually")
            print("   ⏰ Waiting 30 seconds for manual submission...")

            time.sleep(30)

            return True

        except Exception as e:
            print(f"   ❌ Error creating event: {e}")
            return False

    def run_sync(self, limit=3):
        """Run the sync with browser automation"""
        print("🎵 Will's Pub to Gancio Sync - SELENIUM VERSION")
        print("=" * 55)

        if not SELENIUM_AVAILABLE:
            return

        # Scrape events first
        events = self.scrape_events_simple(limit=limit)

        if not events:
            print("❌ No events found")
            return

        print(f"\n✨ Found {len(events)} events to sync")

        # Show events
        for i, event in enumerate(events, 1):
            print(f"{i}. {event.get('title', 'No title')}")
            print(
                f"   📅 {event.get('parsed_date', 'No date')} at {event.get('parsed_time', 'No time')}"
            )
            print(f"   📍 {event.get('venue', 'No venue')}")

        proceed = input(f"\nProceed with browser automation? (y/N): ").strip().lower()

        if proceed != "y":
            print("👋 Sync cancelled")
            return

        # Start browser automation
        if not self.start_browser():
            return

        try:
            if not self.login_to_gancio():
                return

            # Create events
            print(f"\n🚀 Creating events...")
            for i, event in enumerate(events, 1):
                print(f"\n[{i}/{len(events)}]")
                self.create_event_in_browser(event)
                time.sleep(2)

            print(f"\n✨ Browser automation complete!")
            print(f"   📋 Please check your Gancio admin for created events")

        finally:
            if self.driver:
                input("Press Enter to close browser...")
                self.driver.quit()


def main():
    if not SELENIUM_AVAILABLE:
        print("❌ This script requires Selenium for browser automation")
        print("\n📦 Install requirements:")
        print("   pip install selenium")
        print("   # Install ChromeDriver from https://chromedriver.chromium.org/")
        print("\n💡 Alternative: Use the manual event creation in your admin panel")
        return

    syncer = SeleniumGancioSync("https://orlandopunx.com")
    syncer.run_sync(limit=3)


if __name__ == "__main__":
    main()
