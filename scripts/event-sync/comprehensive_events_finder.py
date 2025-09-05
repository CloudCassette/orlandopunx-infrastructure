#!/usr/bin/env python3
"""
Comprehensive search for all 849 events on the Gancio admin page
"""

import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def find_all_events():
    print("🔍 COMPREHENSIVE SEARCH FOR ALL 849 EVENTS")
    print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # Login
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
        
        # Go to admin
        driver.get("http://localhost:13120/admin")
        time.sleep(5)
        
        print("🎯 Finding and clicking Events section...")
        
        # Try to click Events to activate that section/tab
        badge_elements = driver.find_elements(By.CSS_SELECTOR, ".v-badge")
        for badge in badge_elements:
            if "events" in badge.text.lower() and "849" in badge.text:
                # Try to find and click the Events tab/button
                try:
                    # Look for clickable elements containing "Events"
                    clickable_events = driver.find_elements(By.XPATH, "//*[contains(text(), 'EVENTS') or contains(text(), 'Events')]")
                    for elem in clickable_events:
                        try:
                            driver.execute_script("arguments[0].click();", elem)
                            print(f"✅ Clicked Events element: {elem.tag_name}")
                            time.sleep(2)
                            break
                        except:
                            continue
                except:
                    pass
                break
        
        # Now search extensively for events data
        print("\n📊 COMPREHENSIVE EVENT SEARCH")
        print("-" * 40)
        
        all_potential_events = []
        
        # Strategy 1: Look for Vue.js data tables (v-data-table)
        print("🔍 Strategy 1: Vue.js data tables...")
        data_tables = driver.find_elements(By.CSS_SELECTOR, ".v-data-table, [class*='data-table']")
        
        for i, table in enumerate(data_tables):
            rows = table.find_elements(By.CSS_SELECTOR, "tr, .v-data-table__row")
            print(f"   Data table {i+1}: {len(rows)} rows")
            
            for j, row in enumerate(rows[:10]):  # Check first 10 rows
                text = row.text.strip()
                if text and len(text) > 10 and not any(skip in text.lower() for skip in ['select', 'actions', 'header']):
                    all_potential_events.append({
                        'text': text,
                        'element': row,
                        'source': f'data-table-{i+1}-row-{j+1}'
                    })
                    print(f"     Row {j+1}: {text[:80]}...")
        
        # Strategy 2: Look for regular tables
        print("\n🔍 Strategy 2: Regular HTML tables...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        for i, table in enumerate(tables):
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) > 1:  # Skip tables with only header
                print(f"   Table {i+1}: {len(rows)} rows")
                
                for j, row in enumerate(rows[1:11]):  # Skip header, check first 10
                    text = row.text.strip()
                    if text and len(text) > 10:
                        all_potential_events.append({
                            'text': text,
                            'element': row,
                            'source': f'table-{i+1}-row-{j+1}'
                        })
                        print(f"     Row {j+1}: {text[:80]}...")
        
        # Strategy 3: Look for Vue.js lists
        print("\n🔍 Strategy 3: Vue.js lists...")
        v_lists = driver.find_elements(By.CSS_SELECTOR, ".v-list, .v-list-item-group")
        
        for i, v_list in enumerate(v_lists):
            items = v_list.find_elements(By.CSS_SELECTOR, ".v-list-item")
            if len(items) > 1:
                print(f"   Vue list {i+1}: {len(items)} items")
                
                for j, item in enumerate(items[:10]):
                    text = item.text.strip()
                    if text and len(text) > 10:
                        all_potential_events.append({
                            'text': text,
                            'element': item,
                            'source': f'v-list-{i+1}-item-{j+1}'
                        })
                        print(f"     Item {j+1}: {text[:80]}...")
        
        # Strategy 4: Look for cards
        print("\n🔍 Strategy 4: Cards and containers...")
        cards = driver.find_elements(By.CSS_SELECTOR, ".v-card, .card, [class*='card']")
        
        for i, card in enumerate(cards):
            text = card.text.strip()
            if text and len(text) > 20 and len(text) < 1000:  # Reasonable content size
                all_potential_events.append({
                    'text': text,
                    'element': card,
                    'source': f'card-{i+1}'
                })
                print(f"   Card {i+1}: {text[:100]}...")
        
        # Strategy 5: Brute force - check all divs with substantial content
        print("\n🔍 Strategy 5: All content divs...")
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        content_divs = []
        
        for div in all_divs:
            text = div.text.strip()
            # Look for divs with content that might be events
            if (len(text) > 30 and len(text) < 500 and  # Reasonable size
                not any(skip in text.lower() for skip in [
                    'orlando punk shows', 'digital poster', 'navigation', 'menu', 
                    'header', 'footer', 'sidebar', 'baseurl configured'
                ])):
                content_divs.append(div)
        
        print(f"   Found {len(content_divs)} potential content divs")
        
        for i, div in enumerate(content_divs[:20]):  # Check first 20
            text = div.text.strip()
            all_potential_events.append({
                'text': text,
                'element': div,
                'source': f'content-div-{i+1}'
            })
            print(f"     Div {i+1}: {text[:80]}...")
        
        # Strategy 6: Look for pagination and try to load more
        print("\n🔍 Strategy 6: Looking for pagination...")
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, 
            ".v-pagination, .pagination, .v-btn:contains('next'), .v-btn:contains('more'), button:contains('next')")
        
        if pagination_elements:
            print(f"   Found {len(pagination_elements)} pagination elements")
            for elem in pagination_elements[:3]:
                try:
                    print(f"   Pagination element: {elem.tag_name} - {elem.text}")
                except:
                    pass
        
        # Summary
        print(f"\n📊 SEARCH RESULTS SUMMARY")
        print("-" * 30)
        print(f"Total potential events found: {len(all_potential_events)}")
        
        # Group by source type
        by_source = {}
        for event in all_potential_events:
            source_type = event['source'].split('-')[0]
            if source_type not in by_source:
                by_source[source_type] = []
            by_source[source_type].append(event)
        
        for source_type, events in by_source.items():
            print(f"   {source_type}: {len(events)} events")
        
        # Look for duplicates in our findings
        print(f"\n🔍 DUPLICATE ANALYSIS")
        print("-" * 20)
        
        from collections import defaultdict
        import re
        
        # Simple duplicate detection
        normalized_texts = defaultdict(list)
        
        for event in all_potential_events:
            # Normalize the text for comparison
            text = event['text']
            normalized = re.sub(r'[^\w\s]', '', text.lower())
            normalized = re.sub(r'\s+', ' ', normalized.strip())
            
            # Use first few words as key
            words = normalized.split()[:5]  # First 5 words
            if len(words) >= 2:  # Must have at least 2 words
                key = ' '.join(words)
                normalized_texts[key].append(event)
        
        # Find duplicates
        duplicates = {k: v for k, v in normalized_texts.items() if len(v) > 1}
        
        if duplicates:
            print(f"✅ Found {len(duplicates)} groups of potential duplicates:")
            for key, events in list(duplicates.items())[:5]:  # Show first 5 groups
                print(f"   Group: '{key}...' - {len(events)} copies")
                for event in events[:2]:  # Show first 2 in each group
                    print(f"     {event['source']}: {event['text'][:50]}...")
        else:
            print("⚠️ No obvious duplicates found in current results")
        
        # Save page source for further analysis
        with open("/tmp/admin_full_page.html", "w") as f:
            f.write(driver.page_source)
        print("\n💾 Saved full admin page to /tmp/admin_full_page.html")
        
        return len(all_potential_events)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0
        
    finally:
        driver.quit()

if __name__ == "__main__":
    total_found = find_all_events()
    print(f"\n🎯 FINAL RESULT: Found {total_found} potential events")
    if total_found > 0 and total_found < 849:
        print("💡 There are likely more events that require pagination or different navigation")
    elif total_found == 0:
        print("💡 Events may be loaded dynamically or require specific user interactions")
