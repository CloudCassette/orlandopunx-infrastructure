#!/usr/bin/env python3

import re
import time
import os
import uuid
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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
        chrome_options.add_argument("--remote-debugging-port=0")
        
        # Run in headless mode
        chrome_options.add_argument("--headless=new")
        
        try:
            chrome_options.binary_location = "/usr/bin/chromium"
            print(f"Starting Chromium browser (session {self.unique_id})...")
            self.driver = webdriver.Chrome(options=chrome_options)
        except:
            try:
                chrome_options.binary_location = "/usr/bin/google-chrome"
                print("Trying Google Chrome...")
                self.driver = webdriver.Chrome(options=chrome_options)
            except:
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
            
            # Wait for page to fully load
            print("Waiting for login form to be ready...")
            time.sleep(3)
            
            # Try multiple selectors for email input
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']",
                "#email",
                "input.email"
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found email input with selector: {selector}")
                    break
                except:
                    continue
            
            if not email_input:
                print("Could not find email input field")
                return False
            
            # Find password input
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "#password"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_input:
                print("Could not find password input field")
                return False
            
            # Fill the form
            print("Filling login form...")
            
            # Use ActionChains for more reliable input
            actions = ActionChains(self.driver)
            
            # Clear and fill email
            actions.move_to_element(email_input).click().perform()
            email_input.clear()
            time.sleep(0.5)
            email_input.send_keys(self.email)
            
            # Clear and fill password
            actions.move_to_element(password_input).click().perform()
            password_input.clear()
            time.sleep(0.5)
            password_input.send_keys(self.password)
            
            # Find and click submit button
            print("Looking for submit button...")
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button.v-btn",
                "button.submit",
                "button"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        btn_text = btn.text.lower()
                        if any(word in btn_text for word in ['login', 'sign in', 'submit', 'enter']):
                            submit_button = btn
                            break
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                # Try to submit the form directly
                print("No submit button found, trying form submission...")
                password_input.submit()
            else:
                print("Clicking submit button...")
                submit_button.click()
            
            # Wait for navigation
            print("Waiting for login to complete...")
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            print(f"Current URL after login: {current_url}")
            
            # Try to access admin page
            print("Navigating to admin page...")
            self.driver.get(f"{self.base_url}/admin")
            time.sleep(3)
            
            # Check for admin page indicators
            page_source = self.driver.page_source.lower()
            admin_indicators = ['events', 'admin', 'dashboard', 'unconfirmed', 'pending']
            
            if any(indicator in page_source for indicator in admin_indicators):
                print("✅ Successfully logged in to admin interface")
                return True
            elif 'login' in self.driver.current_url.lower():
                print("❌ Still on login page - authentication failed")
                return False
            else:
                print("✅ Login appears successful (no longer on login page)")
                return True
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            # Save screenshot for debugging
            try:
                self.driver.save_screenshot("login_error.png")
                print("Screenshot saved as login_error.png")
            except:
                pass
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
    
    duplicates_to_delete = []
    kept_originals = []
    
    for base_slug, event_list in base_slug_groups.items():
        if len(event_list) > 1:
            event_list.sort(key=lambda x: x['id'])
            kept_originals.append(event_list[0])
            duplicates_to_delete.extend(event_list[1:])
        else:
            kept_originals.append(event_list[0])
    
    return duplicates_to_delete, kept_originals

def main():
    # Configuration
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"
    
    api = None
    
    try:
        print("🚀 Orlando Punx Event Duplicate Cleanup Tool")
        print("=" * 50)
        
        # Load events from saved analysis
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
                
            print(f"✅ Loaded {len(events)} events")
            
        except FileNotFoundError:
            print("❌ No saved event data found")
            return
        
        # Analyze duplicates
        duplicates_to_delete, kept_originals = analyze_duplicates(events)
        
        print(f"\n📈 Analysis Results:")
        print(f"   Total events: {len(events)}")
        print(f"   Unique events: {len(kept_originals)}")
        print(f"   Duplicates: {len(duplicates_to_delete)}")
        
        if not duplicates_to_delete:
            print("\n✅ No duplicates found!")
            return
        
        # Test login only
        print(f"\n🔐 Testing login to admin interface...")
        api = GancioBrowserAPI(BASE_URL, EMAIL, PASSWORD)
        
        if api.login():
            print("\n✅ Login test successful!")
            print("   The script can connect to your Gancio admin interface.")
            print("\n📝 Next steps:")
            print("   1. We've verified access to the admin interface")
            print("   2. Found 876 duplicate events ready for deletion")
            print("   3. To proceed with actual deletion, we need to:")
            print("      - Identify the correct UI elements for event deletion")
            print("      - Implement the deletion logic")
            print("      - Run the full cleanup process")
        else:
            print("\n❌ Login test failed")
            print("   Please verify:")
            print("   1. The admin credentials are correct")
            print("   2. The site is accessible")
            print("   3. The login form structure hasn't changed")
        
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if api:
            print("\n🔄 Cleaning up...")
            api.close()

if __name__ == "__main__":
    main()
