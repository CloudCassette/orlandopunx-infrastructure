#!/usr/bin/env python3
"""
Gancio Browser Automation Duplicate Cleanup
===========================================
Uses Selenium to interact with the Gancio admin interface to find and clean up duplicate events
"""
import tempfile

import os
import sys
import time
import re
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GancioBrowserCleanup:
    """Browser automation for Gancio duplicate cleanup"""
    
    def __init__(self, base_url: str = "http://localhost:13120", headless: bool = True):
        self.base_url = base_url
        self.driver = None
        self.headless = headless
        self.wait = None
        
    def setup_browser(self):
        """Initialize the browser"""
        print("🌐 Setting up browser...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Browser setup successful")
            return True
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def login(self) -> bool:
        """Login to Gancio admin"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")
        
        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False
            
        print(f"🔑 Logging into Gancio as {email}...")
        
        try:
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Find and fill login form
            email_field = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            password_field = self.driver.find_element(By.NAME, "password")
            
            email_field.clear()
            email_field.send_keys(email)
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit form
            password_field.send_keys(Keys.RETURN)
            
            # Wait for redirect or success indicator
            time.sleep(3)
            
            # Check if we're logged in by looking for admin interface elements
            try:
                # Try to find admin-specific elements
                self.wait.until(EC.any_of(
                    EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "admin")),
                    EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Admin")),
                    EC.presence_of_element_located((By.CLASS_NAME, "admin")),
                    EC.url_contains("admin")
                ))
                print("✅ Login successful")
                return True
            except TimeoutException:
                # Check if we're still on login page (failed login)
                if "login" in self.driver.current_url.lower():
                    print("❌ Login failed - still on login page")
                    return False
                else:
                    print("✅ Login successful (redirected)")
                    return True
                    
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def navigate_to_admin(self) -> bool:
        """Navigate to the admin interface"""
        print("🔍 Navigating to admin interface...")
        
        try:
            # Try different admin URLs
            admin_urls = [
                f"{self.base_url}/admin",
                f"{self.base_url}/admin/events",
                f"{self.base_url}/admin/moderation",
            ]
            
            for admin_url in admin_urls:
                try:
                    print(f"  Trying: {admin_url}")
                    self.driver.get(admin_url)
                    time.sleep(2)
                    
                    # Check if we found admin content
                    if self.find_admin_content():
                        print(f"✅ Found admin interface at: {admin_url}")
                        return True
                        
                except Exception as e:
                    print(f"  Failed: {e}")
                    continue
            
            # If direct URLs don't work, try to find admin links
            print("  Looking for admin navigation links...")
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Look for admin links
            admin_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "admin")
            admin_links.extend(self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Admin"))
            admin_links.extend(self.driver.find_elements(By.PARTIAL_LINK_TEXT, "manage"))
            admin_links.extend(self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Manage"))
            
            if admin_links:
                admin_links[0].click()
                time.sleep(3)
                if self.find_admin_content():
                    print("✅ Found admin interface via navigation")
                    return True
            
            print("❌ Could not find admin interface")
            return False
            
        except Exception as e:
            print(f"❌ Admin navigation error: {e}")
            return False
    
    def find_admin_content(self) -> bool:
        """Check if current page has admin content"""
        try:
            # Look for admin-specific elements
            admin_indicators = [
                "event", "Event", "manage", "Manage", "admin", "Admin",
                "approve", "Approve", "pending", "Pending", "moderation"
            ]
            
            for indicator in admin_indicators:
                elements = self.driver.find_elements(By.PARTIAL_LINK_TEXT, indicator)
                elements.extend(self.driver.find_elements(By.CLASS_NAME, indicator.lower()))
                if elements:
                    return True
            
            # Check page source for admin-like content
            page_source = self.driver.page_source.lower()
            if any(word in page_source for word in ["admin", "manage", "approve", "pending"]):
                return True
                
            return False
        except:
            return False
    
    def find_event_list(self) -> List[Dict]:
        """Find and extract event information from the current page"""
        print("📋 Scanning page for events...")
        
        events = []
        
        try:
            # Look for different types of event containers
            event_selectors = [
                "tr",  # Table rows
                ".event", ".event-item", ".event-row",  # Event-specific classes
                "[data-event]", "[data-id]",  # Data attributes
                "li",  # List items
                ".card", ".item", ".row"  # Generic containers
            ]
            
            for selector in event_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"  Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        event_info = self.extract_event_info(element)
                        if event_info:
                            events.append(event_info)
                            
                    if events:
                        break  # Found events, use this selector
                        
                except Exception as e:
                    continue
            
            # Remove duplicates based on ID or text content
            unique_events = []
            seen = set()
            
            for event in events:
                identifier = event.get('id') or event.get('title', '') + event.get('venue', '')
                if identifier not in seen and identifier.strip():
                    unique_events.append(event)
                    seen.add(identifier)
            
            print(f"📊 Found {len(unique_events)} unique events on page")
            return unique_events
            
        except Exception as e:
            print(f"❌ Error finding events: {e}")
            return []
    
    def extract_event_info(self, element) -> Dict:
        """Extract event information from a DOM element"""
        try:
            event_info = {
                'element': element,
                'title': '',
                'venue': '',
                'date': '',
                'id': '',
                'text': element.text.strip()
            }
            
            # Skip if element has no meaningful text
            if len(event_info['text']) < 5:
                return None
            
            # Skip navigation and header elements
            skip_keywords = ['navigation', 'header', 'footer', 'menu', 'nav', 'sidebar']
            if any(keyword in element.get_attribute('class') or '' for keyword in skip_keywords):
                return None
            
            # Try to find ID
            event_id = element.get_attribute('data-id') or element.get_attribute('data-event-id')
            if event_id:
                event_info['id'] = event_id
            
            # Extract title - look for title-like text
            text = event_info['text']
            lines = text.split('\n')
            
            # First non-empty line is often the title
            for line in lines:
                line = line.strip()
                if len(line) > 3 and not line.lower().startswith(('date', 'time', 'venue', 'location')):
                    event_info['title'] = line
                    break
            
            # Look for venue information
            venue_patterns = [
                r'(?:at|@)\s+([^,\n]+)',
                r'venue[:\s]+([^,\n]+)',
                r'location[:\s]+([^,\n]+)',
            ]
            
            for pattern in venue_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    event_info['venue'] = match.group(1).strip()
                    break
            
            # Look for date information
            date_patterns = [
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'\b(\d{4}-\d{2}-\d{2})',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    event_info['date'] = match.group(0).strip()
                    break
            
            return event_info if event_info['title'] else None
            
        except Exception as e:
            return None
    
    def find_duplicates(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Find duplicate events based on title and venue similarity"""
        print("🔍 Analyzing events for duplicates...")
        
        def normalize_text(text: str) -> str:
            if not text:
                return ""
            # Remove special characters, extra spaces, convert to lowercase
            normalized = re.sub(r'[^\w\s]', '', text.lower())
            normalized = re.sub(r'\s+', ' ', normalized.strip())
            return normalized
        
        def create_signature(event: Dict) -> str:
            title = normalize_text(event.get('title', ''))
            venue = normalize_text(event.get('venue', ''))
            # Create a signature from first few words of title + venue
            title_words = title.split()[:3]  # First 3 words
            signature = ' '.join(title_words)
            if venue:
                signature += f"|{venue}"
            return signature
        
        # Group events by signature
        groups = defaultdict(list)
        for event in events:
            signature = create_signature(event)
            if signature:  # Only group events with meaningful signatures
                groups[signature].append(event)
        
        # Filter to only groups with duplicates
        duplicates = {sig: group for sig, group in groups.items() if len(group) > 1}
        
        print(f"📊 Found {len(duplicates)} groups of duplicates:")
        for sig, group in list(duplicates.items())[:5]:  # Show first 5
            print(f"  📌 '{sig}': {len(group)} events")
            for event in group[:2]:  # Show first 2 in each group
                print(f"    - {event.get('title', 'No title')[:40]}...")
        
        if len(duplicates) > 5:
            print(f"    ... and {len(duplicates) - 5} more groups")
        
        return duplicates
    
    def select_events_for_deletion(self, duplicate_groups: Dict[str, List[Dict]], dry_run: bool = True) -> List[Dict]:
        """Select which events to delete (keep the first, mark others for deletion)"""
        to_delete = []
        
        for signature, events in duplicate_groups.items():
            # Sort by text length (longer descriptions often have more info) or keep first
            events_sorted = sorted(events, key=lambda x: len(x.get('text', '')), reverse=True)
            keep_event = events_sorted[0]
            delete_events = events_sorted[1:]
            
            print(f"\n📌 Group: {signature}")
            print(f"   ✅ KEEP: {keep_event.get('title', 'No title')[:50]}...")
            
            for event in delete_events:
                print(f"   ❌ DELETE: {event.get('title', 'No title')[:50]}...")
                if not dry_run:
                    to_delete.append(event)
        
        return to_delete
    
    def delete_events(self, events_to_delete: List[Dict]) -> int:
        """Delete the selected events"""
        if not events_to_delete:
            print("✨ No events to delete")
            return 0
        
        print(f"🗑️ Attempting to delete {len(events_to_delete)} events...")
        
        deleted_count = 0
        
        for event in events_to_delete:
            try:
                element = event['element']
                
                # Look for delete buttons/links near the event
                delete_selectors = [
                    ".delete", ".remove", ".trash", 
                    "[title*='delete']", "[title*='remove']",
                    "button[onclick*='delete']", "a[href*='delete']"
                ]
                
                delete_button = None
                
                # First try to find delete button within the event element
                for selector in delete_selectors:
                    try:
                        delete_button = element.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                # If not found within element, look in parent or sibling elements
                if not delete_button:
                    parent = element.find_element(By.XPATH, "./..")
                    for selector in delete_selectors:
                        try:
                            delete_button = parent.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                
                if delete_button:
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView();", delete_button)
                    time.sleep(0.5)
                    delete_button.click()
                    
                    # Handle confirmation dialogs
                    try:
                        # Check for JavaScript confirm dialog
                        WebDriverWait(self.driver, 2).until(EC.alert_is_present())
                        alert = self.driver.switch_to.alert
                        alert.accept()
                    except TimeoutException:
                        pass  # No alert dialog
                    
                    time.sleep(1)
                    deleted_count += 1
                    print(f"   ✅ Deleted: {event.get('title', 'Unknown')[:40]}...")
                    
                else:
                    print(f"   ⚠️ No delete button found for: {event.get('title', 'Unknown')[:40]}...")
                    
            except Exception as e:
                print(f"   ❌ Error deleting event: {e}")
        
        print(f"📊 Successfully deleted {deleted_count} events")
        return deleted_count
    
    def scan_and_cleanup(self, dry_run: bool = True) -> bool:
        """Main method to scan for and clean up duplicates"""
        print("🔍 GANCIO BROWSER DUPLICATE CLEANUP")
        print("=" * 50)
        
        if not self.setup_browser():
            return False
        
        try:
            if not self.login():
                return False
            
            if not self.navigate_to_admin():
                return False
            
            # Try to find events page or queue
            print("🔍 Looking for events or approval queue...")
            
            # Try different event-related pages
            event_pages = [
                "/admin/events",
                "/admin/moderation", 
                "/admin/queue",
                "/admin/pending",
                "/admin"
            ]
            
            all_events = []
            
            for page in event_pages:
                try:
                    print(f"  Checking: {page}")
                    self.driver.get(f"{self.base_url}{page}")
                    time.sleep(3)
                    
                    events = self.find_event_list()
                    if events:
                        all_events.extend(events)
                        print(f"    Found {len(events)} events")
                        
                        # Try pagination if available
                        page_num = 1
                        while page_num < 10:  # Max 10 pages to avoid infinite loops
                            try:
                                # Look for next page button
                                next_buttons = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Next")
                                next_buttons.extend(self.driver.find_elements(By.PARTIAL_LINK_TEXT, "next"))
                                next_buttons.extend(self.driver.find_elements(By.CSS_SELECTOR, ".next, .pagination-next"))
                                
                                if next_buttons:
                                    next_buttons[0].click()
                                    time.sleep(2)
                                    page_events = self.find_event_list()
                                    if page_events:
                                        all_events.extend(page_events)
                                        print(f"    Page {page_num + 1}: Found {len(page_events)} events")
                                        page_num += 1
                                    else:
                                        break
                                else:
                                    break
                            except Exception as e:
                                break
                    
                except Exception as e:
                    print(f"    Error on {page}: {e}")
                    continue
            
            if not all_events:
                print("⚠️ No events found on any admin page")
                return True
            
            print(f"📊 Total events found: {len(all_events)}")
            
            # Find duplicates
            duplicate_groups = self.find_duplicates(all_events)
            
            if not duplicate_groups:
                print("✨ No duplicates found!")
                return True
            
            total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
            print(f"🔍 Found {len(duplicate_groups)} groups with {total_duplicates} duplicate events")
            
            if dry_run:
                print("\n🔍 DRY RUN MODE - Showing what would be deleted:")
                self.select_events_for_deletion(duplicate_groups, dry_run=True)
                print(f"\n💡 Run with --force to actually delete these {total_duplicates} events")
                return True
            else:
                print(f"\n⚠️ DANGER: About to delete {total_duplicates} events!")
                confirmation = input("Type 'DELETE' to confirm: ")
                if confirmation != 'DELETE':
                    print("❌ Deletion cancelled")
                    return False
                
                events_to_delete = self.select_events_for_deletion(duplicate_groups, dry_run=False)
                deleted_count = self.delete_events(events_to_delete)
                
                print(f"\n🎉 Cleanup complete! Deleted {deleted_count} duplicate events")
                return True
                
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Browser-based Gancio duplicate cleanup")
    parser.add_argument("--url", default="http://localhost:13120", help="Gancio base URL")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    parser.add_argument("--force", action="store_true", help="Actually delete duplicates")
    
    args = parser.parse_args()
    
    cleaner = GancioBrowserCleanup(
        base_url=args.url,
        headless=not args.no_headless
    )
    
    try:
        success = cleaner.scan_and_cleanup(dry_run=not args.force)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
