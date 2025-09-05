#!/usr/bin/env python3

import re
import time
import os
import uuid
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GancioBrowserAPI:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.driver = None
        self.unique_id = str(uuid.uuid4())[:8]
        
    def start_browser(self):
        """Start browser session with unique configuration"""
        chrome_options = Options()
        
        # Create unique user data directory
        user_data_dir = f"/tmp/chrome_user_data_{self.unique_id}"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Additional Chrome options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=0")  # Use random port
        
        # Try headless mode for better reliability
        chrome_options.add_argument("--headless=new")
        
        try:
            chrome_options.binary_location = "/usr/bin/chromium"
            print(f"Starting Chromium browser (session {self.unique_id})...")
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Failed to start Chromium: {e}")
            try:
                chrome_options.binary_location = "/usr/bin/google-chrome"
                print("Trying Google Chrome...")
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"Failed to start Chrome: {e2}")
                raise Exception("Could not start browser")
        
        # Set timeouts
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        
    def login(self):
        """Login to Gancio admin interface"""
        if not self.driver:
            self.start_browser()
            
        print(f"Navigating to {self.base_url}/login...")
        
        try:
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Fill login form
            print("Filling login form...")
            email_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[placeholder*='email']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            
            email_input.clear()
            email_input.send_keys(self.email)
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Submit login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .v-btn, button")
            login_button.click()
            
            # Wait for redirect/response
            time.sleep(3)
            
            # Check if we're logged in by trying to access admin
            print("Checking admin access...")
            self.driver.get(f"{self.base_url}/admin")
            time.sleep(3)
            
            # Look for admin indicators
            page_source = self.driver.page_source.lower()
            if any(indicator in page_source for indicator in ["events", "admin", "dashboard", "manage"]):
                print("✅ Successfully logged in to admin interface")
                return True
            else:
                print("❌ Login failed - no admin access detected")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def click_events_tab(self):
        """Click on the Events tab to load event interface"""
        try:
            print("Looking for Events interface...")
            
            # Try multiple selectors for Events tab/section
            events_selectors = [
                "//div[contains(@class, 'v-tab') and contains(., 'Events')]",
                "//button[contains(., 'Events')]",
                "//a[contains(., 'Events')]",
                "//div[contains(@class, 'tab') and contains(., 'Events')]",
                "//li[contains(., 'Events')]"
            ]
            
            for selector in events_selectors:
                try:
                    events_element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    events_element.click()
                    time.sleep(3)
                    print("✅ Events section accessed")
                    return True
                except:
                    continue
            
            # If no clickable events tab, we might already be on the right page
            print("No Events tab found, checking if events are already visible...")
            page_source = self.driver.page_source.lower()
            if any(word in page_source for word in ["unconfirmed", "pending", "event", "title", "date"]):
                print("✅ Events interface appears to be loaded")
                return True
            
            print("❌ Could not access Events interface")
            return False
            
        except Exception as e:
            print(f"❌ Error accessing Events: {e}")
            return False
    
    def delete_event_by_id(self, event_id):
        """Delete a specific event by finding and clicking its delete button"""
        try:
            print(f"   Searching for event {event_id} in page...")
            
            # Refresh page to get latest state
            self.driver.refresh()
            time.sleep(2)
            
            # Try to find the event using multiple strategies
            event_found = False
            delete_button = None
            
            # Strategy 1: Look for event ID in text content
            try:
                event_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{event_id}')]")
                if event_elements:
                    print(f"   Found event {event_id} in page content")
                    event_found = True
                    
                    # Look for delete button near the event
                    for element in event_elements:
                        # Check parent and sibling elements for delete buttons
                        parent = element.find_element(By.XPATH, "..")
                        delete_candidates = parent.find_elements(By.XPATH, ".//button[contains(@class, 'delete') or contains(., 'Delete') or contains(., 'Remove') or contains(@class, 'trash') or contains(@class, 'remove')]")
                        
                        if delete_candidates:
                            delete_button = delete_candidates[0]
                            break
            except:
                pass
            
            # Strategy 2: Look for data attributes
            if not delete_button:
                try:
                    delete_candidates = self.driver.find_elements(By.XPATH, f"//*[@data-id='{event_id}']//button[contains(@class, 'delete') or contains(., 'Delete')]")
                    if delete_candidates:
                        delete_button = delete_candidates[0]
                        event_found = True
                except:
                    pass
            
            # Strategy 3: Look in table rows
            if not delete_button:
                try:
                    rows = self.driver.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        if event_id in row.text:
                            delete_candidates = row.find_elements(By.XPATH, ".//button[contains(@class, 'delete') or contains(., 'Delete') or contains(., 'Remove')]")
                            if delete_candidates:
                                delete_button = delete_candidates[0]
                                event_found = True
                                break
                except:
                    pass
            
            if not event_found:
                print(f"   ❌ Event {event_id} not found in current page")
                return False
            
            if not delete_button:
                print(f"   ❌ No delete button found for event {event_id}")
                return False
            
            # Click the delete button
            print(f"   Clicking delete button for event {event_id}")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
            time.sleep(0.5)
            delete_button.click()
            
            # Handle confirmation dialog
            try:
                print("   Looking for confirmation dialog...")
                confirm_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Confirm') or contains(., 'Yes') or contains(., 'Delete') or contains(., 'OK') or contains(@class, 'confirm')]"))
                )
                confirm_button.click()
                print("   Confirmed deletion")
            except:
                print("   No confirmation dialog found - deletion might be direct")
            
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"   ❌ Error deleting event {event_id}: {e}")
            return False
    
    def close(self):
        """Close the browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        # Cleanup temp directory
        user_data_dir = f"/tmp/chrome_user_data_{self.unique_id}"
        try:
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except:
            pass

def analyze_duplicates(events):
    """Analyze events for duplicates based on slug patterns"""
    base_slug_groups = defaultdict(list)
    
    for event in events:
        base_slug = re.sub(r'-\d+$', '', event['slug'])
        base_slug_groups[base_slug].append(event)
    
    # Find duplicates - keep the first one, mark others for deletion
    duplicates_to_delete = []
    kept_originals = []
    
    for base_slug, event_list in base_slug_groups.items():
        if len(event_list) > 1:
            # Sort by ID to keep the earliest one
            event_list.sort(key=lambda x: x['id'])
            kept_originals.append(event_list[0])
            duplicates_to_delete.extend(event_list[1:])  # All but the first
        else:
            kept_originals.append(event_list[0])
    
    return duplicates_to_delete, kept_originals

def main():
    # Configuration
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"
    
    # Start with small batch for testing
    MAX_DELETIONS = 3
    
    api = None
    
    try:
        print("🚀 Orlando Punx Event Duplicate Cleanup Tool")
        print("=" * 50)
        
        # Get events from saved analysis
        print("\n📊 Loading events from previous analysis...")
        events = []
        
        try:
            with open('admin_after_click.html', 'r') as f:
                html_content = f.read()
                
            pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
            matches = re.findall(pattern, html_content)
            
            for match in matches:
                event_id, title_var, slug = match
                events.append({
                    'id': int(event_id),
                    'title_var': title_var,
                    'slug': slug
                })
                
            print(f"✅ Loaded {len(events)} events from saved analysis")
            
        except FileNotFoundError:
            print("❌ No saved event data found (admin_after_click.html missing)")
            print("   Please save the admin page HTML first.")
            return
        
        if not events:
            print("❌ No events found in saved data")
            return
            
        # Analyze duplicates
        duplicates_to_delete, kept_originals = analyze_duplicates(events)
        
        print(f"\n📈 Duplicate Analysis Results:")
        print(f"   📊 Total events: {len(events)}")
        print(f"   💾 Unique events to keep: {len(kept_originals)}")
        print(f"   🗑️  Duplicate events to delete: {len(duplicates_to_delete)}")
        
        if not duplicates_to_delete:
            print("\n✅ No duplicates found! Your event calendar is clean.")
            return
        
        # Show what will be deleted
        print(f"\n🎯 First {MAX_DELETIONS} events to be deleted:")
        target_deletions = duplicates_to_delete[:MAX_DELETIONS]
        for i, event in enumerate(target_deletions):
            print(f"   {i+1}. ID: {event['id']}, Slug: {event['slug'][:70]}...")
        
        # Get user confirmation
        print(f"\n⚠️  This will delete {MAX_DELETIONS} duplicate events from your Gancio site.")
        print(f"   Estimated cleanup time: ~{MAX_DELETIONS * 10} seconds")
        
        response = input(f"\nProceed with deletion? (type 'YES' to continue): ")
        if response != 'YES':
            print("✅ Operation cancelled. No events were deleted.")
            return
        
        # Start browser-based deletion
        print(f"\n🚀 Starting automated cleanup process...")
        api = GancioBrowserAPI(BASE_URL, EMAIL, PASSWORD)
        
        if not api.login():
            print("❌ Failed to login. Please check credentials.")
            return
        
        if not api.click_events_tab():
            print("❌ Could not access Events admin interface")
            return
        
        # Perform deletions
        print(f"\n🗑️  Deleting {len(target_deletions)} duplicate events...")
        deleted_count = 0
        failed_count = 0
        
        for i, event in enumerate(target_deletions):
            print(f"\n[{i+1}/{len(target_deletions)}] Processing event {event['id']}")
            
            if api.delete_event_by_id(event['id']):
                deleted_count += 1
                print(f"   ✅ Successfully deleted")
            else:
                failed_count += 1
                print(f"   ❌ Failed to delete")
            
            # Delay between deletions
            if i < len(target_deletions) - 1:
                print("   ⏳ Waiting 5 seconds before next deletion...")
                time.sleep(5)
        
        # Results summary
        print(f"\n📊 Cleanup Results:")
        print(f"   ✅ Successfully deleted: {deleted_count}")
        print(f"   ❌ Failed to delete: {failed_count}")
        print(f"   🔄 Remaining duplicates: {len(duplicates_to_delete) - deleted_count}")
        
        if deleted_count > 0:
            print(f"\n🎉 Success! Removed {deleted_count} duplicate events from your calendar.")
            
            if len(duplicates_to_delete) > MAX_DELETIONS:
                remaining = len(duplicates_to_delete) - deleted_count
                print(f"   📝 Note: {remaining} duplicates remain.")
                print(f"   💡 Run this script again to continue cleanup, or increase MAX_DELETIONS.")
                print(f"   🕐 Estimated time for full cleanup: ~{(remaining * 10) // 60} minutes")
        else:
            print(f"\n⚠️  No events were successfully deleted.")
            print(f"   🔧 This might indicate changes in the admin interface structure.")
        
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if api:
            print(f"\n🔄 Cleaning up browser session...")
            api.close()

if __name__ == "__main__":
    main()
