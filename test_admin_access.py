#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import sys

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
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        print("✓ Chromium WebDriver started successfully")
        return driver
    except Exception as e:
        print(f"ERROR: Could not start Chromium WebDriver: {e}")
        sys.exit(1)

def login_and_find_admin():
    """Login to Gancio and find the admin interface"""
    config = {
        'BASE_URL': 'https://orlandopunx.com',
        'EMAIL': 'godlessamericarecords@gmail.com',
        'PASSWORD': 'Marmalade-Stapling-Watch7'
    }
    
    driver = setup_driver(headless=True)
    
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
        print(f"✓ Login completed, redirected to: {driver.current_url}")
        
        # Try different admin URLs
        admin_urls_to_try = [
            "/admin",
            "/admin/",
            "/admin/events",
            "/admin/dashboard",
            "/manage",
            "/manage/",
            "/manage/events",
            "/dashboard"
        ]
        
        for admin_path in admin_urls_to_try:
            admin_url = config['BASE_URL'] + admin_path
            print(f"\nTrying admin URL: {admin_url}")
            
            try:
                driver.get(admin_url)
                time.sleep(3)
                
                print(f"  Title: {driver.title}")
                print(f"  URL: {driver.current_url}")
                
                # Look for admin-specific elements
                badges = driver.find_elements(By.XPATH, "//div[contains(@class, 'v-badge')]")
                if badges:
                    print(f"  ✓ Found {len(badges)} badge elements!")
                    for i, badge in enumerate(badges):
                        badge_text = badge.text.strip()
                        print(f"    Badge {i}: '{badge_text}'")
                
                # Look for event-related elements
                tables = driver.find_elements(By.CLASS_NAME, "v-data-table")
                if tables:
                    print(f"  ✓ Found {len(tables)} data tables!")
                
                # Look for any elements with "event" in the text
                event_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'event') or contains(text(), 'Event')]")
                if event_elements:
                    print(f"  ✓ Found {len(event_elements)} elements mentioning events")
                    for elem in event_elements[:3]:  # Show first 3
                        print(f"    Event element: '{elem.text[:50]}...'")
                
                # If we found badges or tables, this might be the admin page
                if badges or tables:
                    print(f"  🎯 This looks promising! Admin interface found at: {admin_url}")
                    
                    # Save page source for analysis
                    with open("admin_page_source.html", "w") as f:
                        f.write(driver.page_source)
                    print("  💾 Saved page source to admin_page_source.html")
                    break
                    
            except Exception as e:
                print(f"  ✗ Error accessing {admin_url}: {e}")
                continue
        else:
            print("\n❌ Could not find admin interface at any of the tried URLs")
            
        # Also check the current page (homepage) for any admin links
        print(f"\nChecking homepage for admin links...")
        driver.get(config['BASE_URL'])
        time.sleep(3)
        
        # Look for any links that might lead to admin
        links = driver.find_elements(By.TAG_NAME, "a")
        admin_links = []
        for link in links:
            href = link.get_attribute("href")
            text = link.text.strip()
            if href and any(word in href.lower() for word in ['admin', 'manage', 'dashboard', 'control']):
                admin_links.append((text, href))
            elif text and any(word in text.lower() for word in ['admin', 'manage', 'dashboard', 'control']):
                admin_links.append((text, href))
        
        if admin_links:
            print(f"Found {len(admin_links)} potential admin links:")
            for text, href in admin_links:
                print(f"  '{text}' -> {href}")
        else:
            print("No obvious admin links found on homepage")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    login_and_find_admin()
