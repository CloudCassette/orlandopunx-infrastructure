#!/usr/bin/env python3
"""
Working Gancio Browser Duplicate Cleanup
========================================
Uses correct selectors for the Vue.js-based Gancio interface
"""

import os
import sys
import time
import tempfile
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class WorkingGancioCleanup:
    """Working browser automation for Gancio with correct selectors"""
    
    def __init__(self, base_url="http://localhost:13120", headless=True):
        self.base_url = base_url
        self.driver = None
        self.headless = headless
        self.wait = None
        
    def setup_browser(self):
        """Initialize browser with correct settings"""
        print("🌐 Setting up browser...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Browser setup successful")
            return True
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def login(self):
        """Login using the correct Vue.js selectors"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")
        
        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False
            
        print(f"🔑 Logging in as {email}...")
        
        try:
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login")
            time.sleep(3)  # Wait for Vue.js to render
            
            # Find email field using type selector (more reliable than ID)
            email_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            
            # Find password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            print("✅ Found login form fields")
            
            # Clear and fill fields
            email_field.clear()
            email_field.send_keys(email)
            
            password_field.clear()
            password_field.send_keys(password)
            
            print("✅ Filled login form")
            
            # Find and click submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            print("🚀 Submitted login form")
            
            # Wait for redirect
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed - still on login page")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def find_admin_interface(self):
        """Navigate to admin interface"""
        print("🔧 Looking for admin interface...")
        
        # Try common admin paths
        admin_paths = ["/admin", "/admin/events", "/user", "/profile"]
        
        for path in admin_paths:
            try:
                print(f"  Trying {path}...")
                self.driver.get(f"{self.base_url}{path}")
                time.sleep(3)
                
                # Check if this page has event management content
                page_source = self.driver.page_source.lower()
                if any(word in page_source for word in ["event", "manage", "moderation", "approve"]):
                    print(f"✅ Found admin content at {path}")
                    return True
                    
            except Exception as e:
                print(f"  ❌ Error accessing {path}: {e}")
                continue
        
        # If direct paths don't work, look for admin links
        print("  Looking for admin links on main page...")
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Look for various admin-related links
            admin_selectors = [
                "a[href*='admin']",
                "a[href*='manage']",
                "a[href*='profile']",
                "a[href*='user']",
                "a:contains('Admin')",
                "a:contains('Manage')"
            ]
            
            for selector in admin_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if links:
                        print(f"✅ Found admin link: {links[0].get_attribute('href')}")
                        links[0].click()
                        time.sleep(3)
                        return True
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ Error looking for admin links: {e}")
        
        print("❌ Could not find admin interface")
        return False
    
    def scan_for_events(self):
        """Scan current page for events"""
        print("📋 Scanning for events...")
        
        events = []
        
        try:
            # Wait for page to load
            time.sleep(3)
            
            # Try different approaches to find events
            event_containers = []
            
            # Look for table rows (common in admin interfaces)
            rows = self.driver.find_elements(By.TAG_NAME, "tr")
            if len(rows) > 1:  # More than just header
                print(f"  Found {len(rows)} table rows")
                event_containers.extend(rows[1:])  # Skip header
            
            # Look for card/item containers
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".card, .item, .event-item")
            if cards:
                print(f"  Found {len(cards)} card elements")
                event_containers.extend(cards)
            
            # Look for list items
            list_items = self.driver.find_elements(By.CSS_SELECTOR, "li:not([class*='nav']):not([class*='menu'])")
            if list_items:
                print(f"  Found {len(list_items)} list items")
                event_containers.extend(list_items)
            
            # Extract event info from containers
            for container in event_containers:
                try:
                    text = container.text.strip()
                    if len(text) > 10 and not self._is_nav_element(container):
                        event_info = self._extract_event_info(container, text)
                        if event_info:
                            events.append(event_info)
                except:
                    continue
            
            # Remove duplicates
            unique_events = []
            seen = set()
            
            for event in events:
                signature = f"{event['title']}|{event['venue']}"
                if signature not in seen:
                    unique_events.append(event)
                    seen.add(signature)
            
            print(f"📊 Found {len(unique_events)} unique events")
            return unique_events
            
        except Exception as e:
            print(f"❌ Error scanning for events: {e}")
            return []
    
    def _is_nav_element(self, element):
        """Check if element is navigation/UI rather than event content"""
        try:
            classes = element.get_attribute("class") or ""
            parent_classes = element.find_element(By.XPATH, "..").get_attribute("class") or ""
            
            skip_keywords = [
                "nav", "menu", "header", "footer", "sidebar", 
                "button", "control", "toolbar", "breadcrumb"
            ]
            
            return any(keyword in (classes + parent_classes).lower() for keyword in skip_keywords)
        except:
            return False
    
    def _extract_event_info(self, element, text):
        """Extract event information from element"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 1:
                return None
            
            # First line is usually the title
            title = lines[0]
            
            # Skip if it looks like UI text
            ui_keywords = ["login", "logout", "settings", "profile", "home", "admin", "dashboard"]
            if any(keyword in title.lower() for keyword in ui_keywords):
                return None
            
            # Look for venue in subsequent lines
            venue = ""
            for line in lines[1:]:
                if any(word in line.lower() for word in ["at ", "@", "venue", "location"]):
                    venue = line
                    break
            
            # Look for date information
            date = ""
            for line in lines:
                if re.search(r'\d{1,2}[/-]\d{1,2}|\d{4}-\d{2}-\d{2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec', line, re.I):
                    date = line
                    break
            
            return {
                'element': element,
                'title': title,
                'venue': venue,
                'date': date,
                'text': text
            }
            
        except:
            return None
    
    def find_duplicates(self, events):
        """Find duplicate events"""
        print("🔍 Analyzing for duplicates...")
        
        def normalize_title(title):
            # Remove special chars, extra spaces, convert to lowercase
            normalized = re.sub(r'[^\w\s]', '', title.lower())
            return re.sub(r'\s+', ' ', normalized.strip())
        
        groups = defaultdict(list)
        
        for event in events:
            # Create signature from normalized title + venue
            title_norm = normalize_title(event['title'])
            venue_norm = normalize_title(event['venue'])
            
            # Use first 3-4 words of title for grouping
            title_words = title_norm.split()[:4]
            signature = ' '.join(title_words)
            
            if venue_norm:
                signature += f"|{venue_norm}"
            
            groups[signature].append(event)
        
        # Filter to only duplicates
        duplicates = {sig: events for sig, events in groups.items() if len(events) > 1}
        
        print(f"📊 Found {len(duplicates)} groups of duplicates")
        for sig, group in list(duplicates.items())[:3]:
            print(f"  📌 '{sig[:50]}...': {len(group)} events")
        
        return duplicates
    
    def preview_deletion(self, duplicate_groups):
        """Show what would be deleted"""
        print("\n🔍 DUPLICATE CLEANUP PREVIEW")
        print("=" * 50)
        
        total_to_delete = 0
        
        for signature, events in duplicate_groups.items():
            # Sort by text length (keep longest/most detailed)
            events_sorted = sorted(events, key=lambda x: len(x['text']), reverse=True)
            keep_event = events_sorted[0]
            delete_events = events_sorted[1:]
            
            print(f"\n📌 Group: {signature[:60]}...")
            print(f"   ✅ KEEP: {keep_event['title'][:60]}...")
            
            for event in delete_events:
                print(f"   ❌ DELETE: {event['title'][:60]}...")
                total_to_delete += 1
        
        print(f"\n📊 Total events to delete: {total_to_delete}")
        return total_to_delete
    
    def delete_duplicates(self, duplicate_groups, dry_run=True):
        """Actually delete duplicate events"""
        if dry_run:
            return self.preview_deletion(duplicate_groups)
        
        print("\n⚠️ DELETING DUPLICATE EVENTS")
        print("=" * 40)
        
        deleted_count = 0
        
        for signature, events in duplicate_groups.items():
            events_sorted = sorted(events, key=lambda x: len(x['text']), reverse=True)
            keep_event = events_sorted[0]
            delete_events = events_sorted[1:]
            
            print(f"\n📌 Processing: {signature[:50]}...")
            print(f"   ✅ Keeping: {keep_event['title'][:50]}...")
            
            for event in delete_events:
                try:
                    element = event['element']
                    
                    # Look for delete button/link in various ways
                    delete_found = False
                    
                    # Try common delete selectors
                    delete_selectors = [
                        ".delete", ".remove", ".trash", ".fa-trash",
                        "button:contains('Delete')", "a:contains('Delete')",
                        "button[title*='delete']", "a[title*='delete']",
                        "[onclick*='delete']", "[href*='delete']"
                    ]
                    
                    for selector in delete_selectors:
                        try:
                            delete_btn = element.find_element(By.CSS_SELECTOR, selector)
                            if delete_btn:
                                self.driver.execute_script("arguments[0].scrollIntoView();", delete_btn)
                                time.sleep(0.5)
                                delete_btn.click()
                                
                                # Handle confirmation
                                try:
                                    WebDriverWait(self.driver, 2).until(EC.alert_is_present())
                                    alert = self.driver.switch_to.alert
                                    alert.accept()
                                except TimeoutException:
                                    pass
                                
                                time.sleep(1)
                                deleted_count += 1
                                print(f"   ✅ Deleted: {event['title'][:40]}...")
                                delete_found = True
                                break
                        except:
                            continue
                    
                    if not delete_found:
                        print(f"   ⚠️ No delete button found for: {event['title'][:40]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error deleting event: {e}")
        
        print(f"\n🎉 Deletion complete! Removed {deleted_count} events")
        return deleted_count
    
    def run_cleanup(self, dry_run=True):
        """Main cleanup process"""
        print("🧹 GANCIO BROWSER DUPLICATE CLEANUP")
        print("=" * 50)
        
        if not self.setup_browser():
            return False
        
        try:
            # Login
            if not self.login():
                return False
            
            # Find admin interface
            if not self.find_admin_interface():
                return False
            
            # Scan for events
            events = self.scan_for_events()
            if not events:
                print("⚠️ No events found")
                return True
            
            # Find duplicates
            duplicates = self.find_duplicates(events)
            if not duplicates:
                print("✨ No duplicates found!")
                return True
            
            # Delete or preview
            if dry_run:
                self.delete_duplicates(duplicates, dry_run=True)
                print(f"\n💡 Run with --force to actually delete duplicates")
            else:
                print(f"\n⚠️ About to delete duplicate events!")
                confirm = input("Type 'DELETE' to confirm: ")
                if confirm == 'DELETE':
                    self.delete_duplicates(duplicates, dry_run=False)
                else:
                    print("❌ Deletion cancelled")
            
            return True
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Working Gancio browser duplicate cleanup")
    parser.add_argument("--url", default="http://localhost:13120", help="Gancio base URL")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    parser.add_argument("--force", action="store_true", help="Actually delete duplicates")
    
    args = parser.parse_args()
    
    cleaner = WorkingGancioCleanup(
        base_url=args.url,
        headless=not args.no_headless
    )
    
    try:
        success = cleaner.run_cleanup(dry_run=not args.force)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled")
        return 1

if __name__ == "__main__":
    sys.exit(main())
