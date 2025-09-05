#!/usr/bin/env python3

import re
import time
import uuid

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class GancioAnalyzer:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.driver = None
        self.unique_id = str(uuid.uuid4())[:8]

    def start_browser(self):
        """Start browser session"""
        chrome_options = Options()
        user_data_dir = f"/tmp/chrome_user_data_{self.unique_id}"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--headless=new")

        try:
            chrome_options.binary_location = "/usr/bin/chromium"
            print(f"Starting browser session {self.unique_id}...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            print(f"Failed to start browser: {e}")
            return False

    def login(self):
        """Login to admin interface"""
        print(f"Logging in to {self.base_url}...")

        try:
            # Navigate to login
            self.driver.get(f"{self.base_url}/login")
            time.sleep(3)

            # Find and fill email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input.clear()
            email_input.send_keys(self.email)

            # Find and fill password
            password_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password']"
            )
            password_input.clear()
            password_input.send_keys(self.password)

            # Submit form
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "login" in btn.text.lower():
                    btn.click()
                    break
            else:
                password_input.submit()

            # Wait for login
            time.sleep(5)

            # Navigate to admin
            self.driver.get(f"{self.base_url}/admin")
            time.sleep(3)

            print("✅ Logged in successfully")
            return True

        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def capture_events_interface(self):
        """Capture the events interface structure"""
        print("\n📸 Capturing admin interface structure...")

        try:
            # Look for Events tab and click it
            print("Looking for Events tab...")
            events_tab_found = False

            # Try different selectors for Events tab
            tab_selectors = [
                "//div[contains(., 'Events')]",
                "//button[contains(., 'Events')]",
                "//a[contains(., 'Events')]",
                "//span[contains(., 'Events')]",
            ]

            for selector in tab_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            if "events" in elem.text.lower():
                                print(
                                    f"Found Events element: {elem.tag_name} with text '{elem.text}'"
                                )
                                elem.click()
                                events_tab_found = True
                                time.sleep(3)
                                break
                    if events_tab_found:
                        break
                except:
                    continue

            # Save current page
            with open("admin_events_page.html", "w") as f:
                f.write(self.driver.page_source)
            print("✅ Saved admin page as 'admin_events_page.html'")

            # Analyze the page structure
            print("\n🔍 Analyzing page structure...")

            # Look for event elements
            print("\n📋 Looking for event elements...")

            # Check for various event container patterns
            event_patterns = [
                ("Table rows", "tr", ["899", "934", "967"]),
                ("Divs with IDs", "div", ["899", "934", "967"]),
                ("List items", "li", ["899", "934", "967"]),
                ("Cards", "div[class*='card']", ["event", "title"]),
                ("Any element with event ID", "*", ["899"]),
            ]

            for pattern_name, selector, search_terms in event_patterns:
                try:
                    if selector.startswith("*"):
                        elements = self.driver.find_elements(By.XPATH, "//*")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for elem in elements[:100]:  # Check first 100 elements
                        elem_text = elem.text[:200] if elem.text else ""
                        for term in search_terms:
                            if term in elem_text:
                                print(f"✓ Found {pattern_name}: {elem.tag_name}")
                                print(f"  Text preview: {elem_text[:100]}...")

                                # Look for delete buttons nearby
                                try:
                                    parent = elem.find_element(By.XPATH, "..")
                                    buttons = parent.find_elements(
                                        By.TAG_NAME, "button"
                                    )
                                    if buttons:
                                        print(
                                            f"  Found {len(buttons)} button(s) in parent element"
                                        )
                                        for btn in buttons[:3]:
                                            print(
                                                f"    Button: '{btn.text}' | Classes: {btn.get_attribute('class')}"
                                            )
                                except:
                                    pass
                                break
                except:
                    continue

            # Look for buttons that might be delete buttons
            print("\n🔘 Analyzing buttons on the page...")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} total buttons")

            delete_keywords = ["delete", "remove", "trash", "cancel", "reject", "deny"]
            for btn in buttons[:20]:  # Check first 20 buttons
                btn_text = btn.text.lower()
                btn_class = btn.get_attribute("class") or ""
                btn_title = btn.get_attribute("title") or ""

                for keyword in delete_keywords:
                    if (
                        keyword in btn_text
                        or keyword in btn_class.lower()
                        or keyword in btn_title.lower()
                    ):
                        print(f"  Potential delete button found:")
                        print(f"    Text: '{btn.text}'")
                        print(f"    Classes: {btn_class}")
                        print(f"    Title: {btn_title}")
                        break

            # Look for icons that might be delete buttons
            print("\n🎯 Looking for icon buttons...")
            icons = self.driver.find_elements(
                By.CSS_SELECTOR, "i, svg, [class*='icon']"
            )
            print(f"Found {len(icons)} icon elements")

            for icon in icons[:20]:
                icon_class = icon.get_attribute("class") or ""
                parent = icon.find_element(By.XPATH, "..")

                if any(
                    word in icon_class.lower()
                    for word in ["trash", "delete", "remove", "close"]
                ):
                    print(f"  Potential delete icon found:")
                    print(f"    Icon class: {icon_class}")
                    print(f"    Parent tag: {parent.tag_name}")
                    print(f"    Parent class: {parent.get_attribute('class')}")

            # Take a screenshot
            self.driver.save_screenshot("admin_events_interface.png")
            print("\n📷 Screenshot saved as 'admin_events_interface.png'")

            # Try to find a specific event and its controls
            print("\n🎯 Looking for specific event ID 899...")
            event_899_elements = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), '899')]"
            )

            if event_899_elements:
                print(f"Found {len(event_899_elements)} elements containing '899'")
                for elem in event_899_elements[:3]:
                    print(f"\n  Element: {elem.tag_name}")
                    print(f"  Text: {elem.text[:100]}...")

                    # Find nearest buttons
                    parent = elem
                    for _ in range(3):  # Check up to 3 parent levels
                        parent = parent.find_element(By.XPATH, "..")
                        buttons = parent.find_elements(By.TAG_NAME, "button")
                        if buttons:
                            print(f"  Found buttons at parent level:")
                            for btn in buttons:
                                print(
                                    f"    - '{btn.text}' | {btn.get_attribute('class')}"
                                )
                            break

            return True

        except Exception as e:
            print(f"❌ Error capturing interface: {e}")
            import traceback

            traceback.print_exc()
            return False

    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
        # Cleanup temp dir
        import shutil

        shutil.rmtree(f"/tmp/chrome_user_data_{self.unique_id}", ignore_errors=True)


def main():
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"

    analyzer = None
    try:
        print("🔍 Gancio Admin Interface Analyzer")
        print("=" * 50)

        analyzer = GancioAnalyzer(BASE_URL, EMAIL, PASSWORD)

        if not analyzer.start_browser():
            print("Failed to start browser")
            return

        if not analyzer.login():
            print("Failed to login")
            return

        analyzer.capture_events_interface()

        print("\n✅ Analysis complete!")
        print("   Check the following files:")
        print("   - admin_events_page.html (full page source)")
        print("   - admin_events_interface.png (screenshot)")

    except KeyboardInterrupt:
        print("\n❌ Cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if analyzer:
            analyzer.close()


if __name__ == "__main__":
    main()
