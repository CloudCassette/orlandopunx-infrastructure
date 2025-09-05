#!/usr/bin/env python3

import re
import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GancioBrowserAPI:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.driver = None
        
    def start_browser(self):
        """Start browser session"""
        chrome_options = Options()
        # Run in headed mode so we can see what's happening
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.binary_location = "/usr/bin/chromium"
        
        print("Starting Chrome browser...")
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def login(self):
        """Login to Gancio admin interface"""
        if not self.driver:
            self.start_browser()
            
        print(f"Logging in to {self.base_url}...")
        
        # Navigate to login page
        self.driver.get(f"{self.base_url}/login")
        
        # Fill login form
        email_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
        )
        password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
        
        email_input.clear()
        email_input.send_keys(self.email)
        password_input.clear()
        password_input.send_keys(self.password)
        
        # Submit login
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .v-btn")
        login_button.click()
        
        # Wait for redirect
        time.sleep(3)
        
        # Check if we're logged in by trying to access admin
        self.driver.get(f"{self.base_url}/admin")
        time.sleep(2)
        
        # Look for admin indicators
        if "Events" in self.driver.page_source:
            print("✅ Successfully logged in to admin interface")
            return True
        else:
            print("❌ Login failed - no admin access")
            return False
    
    def get_events_from_saved_data(self):
        """Load events from our previously saved analysis"""
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
            return events
            
        except FileNotFoundError:
            print("❌ No saved event data found")
            return []
    
    def click_events_tab(self):
        """Click on the Events tab to load event interface"""
        try:
            print("Clicking on Events tab...")
            # Wait for and click Events tab
            events_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'v-tab') and contains(., 'Events')]"))
            )
            events_tab.click()
            time.sleep(3)
            print("✅ Events tab clicked")
            return True
        except Exception as e:
            print(f"❌ Failed to click Events tab: {e}")
            return False
    
    def delete_event_by_id(self, event_id):
        """Delete a specific event by finding and clicking its delete button"""
        try:
            # Look for the event in the interface
            # This might be in a table, list, or card format
            event_selectors = [
                f"//tr[contains(., '{event_id}')]//button[contains(@class, 'delete') or contains(., 'Delete') or contains(., 'Remove')]",
                f"//div[contains(., '{event_id}')]//button[contains(@class, 'delete') or contains(., 'Delete') or contains(., 'Remove')]",
                f"//*[@data-id='{event_id}']//button[contains(@class, 'delete') or contains(., 'Delete')]",
                f"//*[contains(text(), '{event_id}')]/following::button[contains(@class, 'delete') or contains(., 'Delete')]"
            ]
            
            for selector in event_selectors:
                try:
                    delete_button = self.driver.find_element(By.XPATH, selector)
                    delete_button.click()
                    
                    # Confirm deletion if needed
                    try:
                        confirm_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Confirm') or contains(., 'Yes') or contains(., 'Delete')]"))
                        )
                        confirm_button.click()
                    except:
                        pass  # No confirmation needed
                    
                    time.sleep(1)
                    return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"Error deleting event {event_id}: {e}")
            return False
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

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
    
    # Modes
    DRY_RUN = True  # Set to False to actually delete events
    MAX_DELETIONS = 20  # Limit deletions for safety (can be increased)
    
    api = None
    
    try:
        # Get events from saved analysis
        print("Loading events from previous analysis...")
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
            print("❌ No saved event data found. Please run the browser analysis first.")
            return
        
        if not events:
            print("❌ No events found in saved data")
            return
            
        # Analyze duplicates
        duplicates_to_delete, kept_originals = analyze_duplicates(events)
        
        print(f"\n📈 Duplicate Analysis Results:")
        print(f"   Total events: {len(events)}")
        print(f"   Unique events to keep: {len(kept_originals)}")
        print(f"   Duplicate events to delete: {len(duplicates_to_delete)}")
        
        if not duplicates_to_delete:
            print("✅ No duplicates found!")
            return
        
        # Show detailed breakdown
        print(f"\n🗑️  Events that will be deleted (first {min(15, len(duplicates_to_delete))}):")
        for i, event in enumerate(duplicates_to_delete[:15]):
            print(f"   {i+1}. ID: {event['id']}, Slug: {event['slug']}")
        if len(duplicates_to_delete) > 15:
            print(f"   ... and {len(duplicates_to_delete) - 15} more")
        
        # Show what will be kept
        print(f"\n💾 Original events that will be kept (first 10):")
        for i, event in enumerate(kept_originals[:10]):
            base_slug = re.sub(r'-\d+$', '', event['slug'])
            duplicates_count = len([d for d in duplicates_to_delete if re.sub(r'-\d+$', '', d['slug']) == base_slug])
            if duplicates_count > 0:
                print(f"   {i+1}. ID: {event['id']}, Slug: {event['slug']} (+ {duplicates_count} duplicates will be removed)")
        
        # Confirmation and mode selection
        if DRY_RUN:
            print(f"\n🔍 DRY RUN MODE - No events will actually be deleted")
            print(f"   This analysis shows what WOULD be deleted.")
            print(f"   To perform actual deletions, we need to use the browser interface.")
            
            response = input(f"\nWould you like to proceed with deleting {min(MAX_DELETIONS, len(duplicates_to_delete))} duplicates? (type 'YES' to continue): ")
            if response != 'YES':
                print("✅ Analysis complete. No changes made.")
                return
            
            print("🚀 Starting browser-based deletion process...")
            DRY_RUN = False
        
        if not DRY_RUN:
            # Start browser-based deletion
            api = GancioBrowserAPI(BASE_URL, EMAIL, PASSWORD)
            
            if not api.login():
                print("❌ Failed to login via browser")
                return
            
            # Navigate to Events admin page
            if not api.click_events_tab():
                print("❌ Could not access Events admin interface")
                return
            
            # Delete duplicates (limited for safety)
            deleted_count = 0
            failed_count = 0
            
            target_deletions = duplicates_to_delete[:MAX_DELETIONS]
            print(f"\n🗑️  Deleting {len(target_deletions)} duplicate events...")
            
            for i, event in enumerate(target_deletions):
                print(f"[{i+1}/{len(target_deletions)}] Deleting event {event['id']} ({event['slug'][:50]}...)")
                
                if api.delete_event_by_id(event['id']):
                    deleted_count += 1
                    print(f"   ✅ Deleted")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed")
                
                time.sleep(2)  # Delay between deletions
            
            print(f"\n📊 Cleanup Results:")
            print(f"   Successfully deleted: {deleted_count}")
            print(f"   Failed to delete: {failed_count}")
            print(f"   Remaining duplicates: {len(duplicates_to_delete) - deleted_count}")
            
            if deleted_count > 0:
                print(f"✅ Successfully removed {deleted_count} duplicate events!")
                
                remaining_total = len(events) - deleted_count
                print(f"   Your calendar should now show approximately {remaining_total} events.")
                
                if len(duplicates_to_delete) > MAX_DELETIONS:
                    remaining_dups = len(duplicates_to_delete) - deleted_count
                    print(f"   Note: {remaining_dups} duplicates remain. Run script again to continue cleanup.")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if api:
            api.close()

if __name__ == "__main__":
    main()
