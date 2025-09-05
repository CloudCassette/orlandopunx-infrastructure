#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import sys

def setup_driver(headless=False):  # Let's make it non-headless to see what's happening
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
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        print("✓ Chromium WebDriver started successfully")
        return driver
    except Exception as e:
        print(f"ERROR: Could not start Chromium WebDriver: {e}")
        sys.exit(1)

def inspect_admin_page():
    """Login to Gancio and inspect the admin page in detail"""
    config = {
        'BASE_URL': 'https://orlandopunx.com',
        'EMAIL': 'godlessamericarecords@gmail.com',
        'PASSWORD': 'Marmalade-Stapling-Watch7'
    }
    
    driver = setup_driver(headless=True)  # Use headless since we know it works
    
    try:
        # Login process
        print("Logging in...")
        login_url = f"{config['BASE_URL']}/login"
        driver.get(login_url)
        time.sleep(3)
        
        # Fill login form
        email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_field.send_keys(config['EMAIL'])
        
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.send_keys(config['PASSWORD'])
        
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        login_button.click()
        
        time.sleep(5)
        print(f"✓ Login completed")
        
        # Go to admin page
        admin_url = f"{config['BASE_URL']}/admin"
        print(f"Going to admin page: {admin_url}")
        driver.get(admin_url)
        time.sleep(5)  # Wait longer for the SPA to load
        
        print(f"Admin page title: {driver.title}")
        print(f"Admin page URL: {driver.current_url}")
        
        # Look for all different types of elements
        print("\n=== SEARCHING FOR ADMIN ELEMENTS ===")
        
        # Look for badges (event counts)
        badges = driver.find_elements(By.XPATH, "//div[contains(@class, 'v-badge')]")
        print(f"Badges found: {len(badges)}")
        for i, badge in enumerate(badges):
            try:
                badge_text = badge.text.strip()
                badge_html = badge.get_attribute("outerHTML")[:200]
                print(f"  Badge {i}: text='{badge_text}', html='{badge_html}...'")
            except:
                print(f"  Badge {i}: Could not get text/html")
        
        # Look for any element containing numbers that might be event counts
        number_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '849') or contains(text(), '800') or contains(text(), '8')]")
        print(f"\nElements with potential event counts: {len(number_elements)}")
        for elem in number_elements[:5]:
            try:
                text = elem.text.strip()
                tag = elem.tag_name
                classes = elem.get_attribute("class")
                print(f"  {tag}.{classes}: '{text}'")
            except:
                continue
        
        # Look for data tables
        tables = driver.find_elements(By.CLASS_NAME, "v-data-table")
        print(f"\nData tables found: {len(tables)}")
        
        # Look for any clickable elements that might navigate to events
        clickables = driver.find_elements(By.XPATH, "//*[contains(@class, 'v-btn') or contains(@class, 'clickable') or @role='button']")
        print(f"\nClickable elements found: {len(clickables)}")
        for i, elem in enumerate(clickables[:10]):  # Show first 10
            try:
                text = elem.text.strip()
                classes = elem.get_attribute("class")
                if text and len(text) < 50:
                    print(f"  Clickable {i}: '{text}' (classes: {classes[:50]}...)")
            except:
                continue
        
        # Look for Vue.js components that might contain the events interface
        vue_components = driver.find_elements(By.XPATH, "//*[contains(@class, 'v-')]")
        print(f"\nVue components found: {len(vue_components)}")
        
        # Save full page source for analysis
        with open("full_admin_page.html", "w") as f:
            f.write(driver.page_source)
        print("\n💾 Saved full admin page source to full_admin_page.html")
        
        # Try to find and click any element that might show events
        potential_event_triggers = [
            "//div[contains(text(), 'Events')]",
            "//span[contains(text(), 'Events')]", 
            "//button[contains(text(), 'Events')]",
            "//*[contains(@class, 'v-badge')]",
            "//*[contains(text(), '849')]",
            "//*[contains(text(), '8')]"  # Might be abbreviated
        ]
        
        print("\n=== ATTEMPTING TO CLICK EVENT-RELATED ELEMENTS ===")
        for selector in potential_event_triggers:
            elements = driver.find_elements(By.XPATH, selector)
            print(f"Found {len(elements)} elements for selector: {selector}")
            for i, elem in enumerate(elements):
                try:
                    text = elem.text.strip()
                    if text:
                        print(f"  Element {i}: '{text}'")
                        # Try clicking this element
                        try:
                            elem.click()
                            time.sleep(3)
                            print(f"    ✓ Clicked successfully!")
                            
                            # Check if anything changed
                            new_tables = driver.find_elements(By.CLASS_NAME, "v-data-table")
                            if new_tables:
                                print(f"    🎯 SUCCESS! Now found {len(new_tables)} data tables after clicking!")
                                
                                # Look for the events table we saw in the HTML before
                                rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
                                if rows:
                                    print(f"    📋 Found {len(rows)} table rows!")
                                    for j, row in enumerate(rows[:3]):  # Show first 3
                                        cells = row.find_elements(By.XPATH, ".//td")
                                        if len(cells) >= 3:
                                            title = cells[0].text.strip()
                                            place = cells[1].text.strip()
                                            when = cells[2].text.strip()
                                            print(f"      Row {j}: '{title}' at '{place}' on '{when}'")
                                
                                # We found it! Let's stop here
                                print("🎉 FOUND THE EVENTS TABLE!")
                                return True
                            
                        except Exception as click_error:
                            print(f"    ✗ Click failed: {click_error}")
                except:
                    continue
        
        print("\n❌ Could not find events table after trying all selectors")
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    success = inspect_admin_page()
    if success:
        print("✅ Successfully found the admin events interface!")
    else:
        print("❌ Could not locate the admin events interface")
