#!/usr/bin/env python3

import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import defaultdict

def parse_nuxt_data(html_content):
    """Parse the __NUXT__ JavaScript data from the page"""
    # Find the window.__NUXT__ assignment
    nuxt_match = re.search(r'window\.__NUXT__=\(function[^{]*{[^}]*}[^{]*{([^}]*unconfirmedEvents:\[[^\]]*\])', html_content, re.DOTALL)
    
    if not nuxt_match:
        print("Could not find __NUXT__ data in page")
        return []
    
    print("Found __NUXT__ data, parsing events...")
    
    # Extract event data using regex patterns
    events = []
    
    # Look for event objects in the unconfirmedEvents array
    event_pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
    
    for match in re.finditer(event_pattern, html_content):
        event_id = match.group(1)
        title_ref = match.group(2)  # This is a variable reference like 'aj', 'w', etc.
        slug = match.group(3)
        
        events.append({
            'id': int(event_id),
            'title_ref': title_ref,
            'slug': slug
        })
    
    print(f"Found {len(events)} events in JavaScript data")
    return events

def find_duplicate_patterns(events):
    """Find events that appear to be duplicates based on slug patterns"""
    slug_groups = defaultdict(list)
    
    # Group events by base slug (removing trailing numbers and dashes)
    for event in events:
        base_slug = re.sub(r'-\d+$', '', event['slug'])
        slug_groups[base_slug].append(event)
    
    duplicates = {base_slug: events for base_slug, events in slug_groups.items() if len(events) > 1}
    
    print(f"\nFound {len(duplicates)} event series with duplicates:")
    
    total_duplicates = 0
    for base_slug, duplicate_events in duplicates.items():
        print(f"\n{base_slug}: {len(duplicate_events)} events")
        total_duplicates += len(duplicate_events) - 1  # Keep one, count others as duplicates
        
        # Show first few examples
        for i, event in enumerate(duplicate_events[:5]):
            print(f"  {i+1}. ID: {event['id']}, Slug: {event['slug']}")
        if len(duplicate_events) > 5:
            print(f"  ... and {len(duplicate_events) - 5} more")
    
    print(f"\nTotal duplicate events that could be removed: {total_duplicates}")
    return duplicates

def main():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    print("Starting Chrome browser...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Login first
        print("Logging in to admin interface...")
        driver.get("http://orlandopunx.com/login")
        
        # Wait for and fill login form
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
        )
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
        
        email_input.clear()
        email_input.send_keys("admin")
        password_input.clear()
        password_input.send_keys("OrlandoPunkShows2024!")
        
        # Submit login
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .v-btn")
        login_button.click()
        
        # Wait for redirect and navigate to admin
        time.sleep(3)
        print("Navigating to admin page...")
        driver.get("http://orlandopunx.com/admin")
        
        # Wait for page to load
        time.sleep(5)
        
        # Get page source
        html_content = driver.page_source
        print("Page loaded, parsing events...")
        
        # Parse events from JavaScript data
        events = parse_nuxt_data(html_content)
        
        if events:
            # Find duplicates
            duplicates = find_duplicate_patterns(events)
        else:
            print("No events found in JavaScript data")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
