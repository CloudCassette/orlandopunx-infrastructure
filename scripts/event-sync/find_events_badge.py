#!/usr/bin/env python3
"""
Find the Events badge with 849 events and navigate to that section
"""

import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def find_events_section():
    print("🔍 LOOKING FOR EVENTS BADGE WITH 849 EVENTS")
    print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # Login first
        print("🔑 Logging in...")
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")
        
        driver.get("http://localhost:13120/login")
        time.sleep(3)
        
        email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        email_field.send_keys(email)
        password_field.send_keys(password)
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(5)
        
        print("✅ Logged in successfully")
        
        # Go to admin page
        driver.get("http://localhost:13120/admin")
        time.sleep(5)
        
        print("🔍 Searching for Events badge...")
        
        # Look for the badge with "Events" text and a number
        badge_selectors = [
            ".v-badge",
            "[class*='badge']", 
            ".badge",
            "*:contains('Events')",
            "*:contains('849')"
        ]
        
        events_element = None
        
        for selector in badge_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    text = element.text.strip()
                    if "events" in text.lower() and ("849" in text or any(char.isdigit() for char in text)):
                        print(f"✅ Found Events badge: {text}")
                        events_element = element
                        break
                
                if events_element:
                    break
                    
            except Exception as e:
                print(f"  Error with selector {selector}: {e}")
                continue
        
        if not events_element:
            # Look through all elements for "Events" or numbers
            print("🔍 Searching all elements for Events...")
            all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
            
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if text and ("events" in text.lower() or "849" in text):
                        print(f"📋 Found element with text: {text[:100]}")
                        if "events" in text.lower() and any(char.isdigit() for char in text):
                            events_element = element
                            print(f"✅ Using this as Events element")
                            break
                except:
                    continue
        
        if events_element:
            print(f"🎯 Found Events element, attempting to click...")
            
            # Try to click it
            try:
                driver.execute_script("arguments[0].scrollIntoView();", events_element)
                time.sleep(1)
                events_element.click()
                time.sleep(3)
                
                print("✅ Clicked Events element")
                print(f"📍 Current URL: {driver.current_url}")
                print(f"📍 Page title: {driver.title}")
                
                # Look for events on this new page
                print("🔍 Scanning for individual events...")
                
                # Try different approaches to find event listings
                potential_events = []
                
                # Look for table rows
                rows = driver.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 2:
                    print(f"📊 Found {len(rows)} table rows")
                    for i, row in enumerate(rows[1:6]):  # Skip header, show first 5
                        text = row.text.strip()
                        if text and len(text) > 10:
                            potential_events.append(text)
                            print(f"   Row {i+1}: {text[:80]}...")
                
                # Look for cards or list items
                cards = driver.find_elements(By.CSS_SELECTOR, ".card, .item, .list-item, .event-item")
                if cards:
                    print(f"🎴 Found {len(cards)} card elements")
                    for i, card in enumerate(cards[:5]):
                        text = card.text.strip()
                        if text and len(text) > 10:
                            potential_events.append(text)
                            print(f"   Card {i+1}: {text[:80]}...")
                
                # Look for any divs with substantial content
                divs = driver.find_elements(By.TAG_NAME, "div")
                content_divs = [div for div in divs if len(div.text.strip()) > 20 and len(div.text.strip()) < 300]
                
                if content_divs:
                    print(f"📄 Found {len(content_divs)} content divs")
                    for i, div in enumerate(content_divs[:10]):
                        text = div.text.strip()
                        # Skip if it looks like navigation or repeated content
                        if not any(skip in text.lower() for skip in ['orlando punk shows', 'digital poster', 'menu', 'navigation']):
                            potential_events.append(text)
                            print(f"   Div {i+1}: {text[:80]}...")
                
                print(f"📊 Found {len(potential_events)} potential events")
                
                # Save page source for analysis
                with open("/tmp/events_page_source.html", "w") as f:
                    f.write(driver.page_source)
                print("💾 Saved page source to /tmp/events_page_source.html")
                
            except Exception as e:
                print(f"❌ Error clicking Events element: {e}")
        
        else:
            print("❌ Could not find Events badge element")
            
            # Save current page for analysis
            with open("/tmp/admin_page_source.html", "w") as f:
                f.write(driver.page_source)
            print("💾 Saved admin page source to /tmp/admin_page_source.html")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    find_events_section()
