#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys
import os
import tempfile

def load_config():
    """Load configuration from config.py or use defaults"""
    try:
        import config
        return {
            'BASE_URL': config.BASE_URL,
            'EMAIL': config.EMAIL,
            'PASSWORD': config.PASSWORD,
            'MAX_REMOVALS_PER_PAGE': getattr(config, 'MAX_REMOVALS_PER_PAGE', 5),
            'MAX_PAGES_TO_PROCESS': getattr(config, 'MAX_PAGES_TO_PROCESS', 10),
            'DELAY_BETWEEN_REMOVALS': getattr(config, 'DELAY_BETWEEN_REMOVALS', 3),
            'HEADLESS_MODE': getattr(config, 'HEADLESS_MODE', False),
            'BROWSER_TIMEOUT': getattr(config, 'BROWSER_TIMEOUT', 20)
        }
    except ImportError:
        print("ERROR: config.py not found!")
        print("Please copy config_example.py to config.py and update with your values")
        sys.exit(1)

def setup_driver(headless=False):
    """Setup Chrome WebDriver with minimal options"""
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    # Essential options only
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        print(f"✓ Chrome WebDriver started successfully")
        return driver
    except Exception as e:
        print(f"ERROR: Could not start Chrome WebDriver: {e}")
        print("Make sure Chrome and ChromeDriver are properly installed")
        sys.exit(1)

def login_to_gancio(driver, base_url, email, password, timeout=20):
    """Login to Gancio admin interface"""
    print("Logging in to Gancio...")
    
    login_url = f"{base_url}/login"
    driver.get(login_url)
    
    wait = WebDriverWait(driver, timeout)
    
    try:
        # Wait for login form to load and find email field
        email_field = wait.until(EC.presence_of_element_located((By.ID, "input-45")))
        email_field.clear()
        email_field.send_keys(email)
        
        # Find password field  
        password_field = driver.find_element(By.ID, "input-48")
        password_field.clear()
        password_field.send_keys(password)
        
        # Find and click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        login_button.click()
        
        # Wait for admin page to load (look for badge or admin interface)
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'v-badge')]")))
        print("✓ Login successful!")
        return True
        
    except TimeoutException:
        print("✗ Login failed - timeout waiting for elements")
        return False
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return False

def navigate_to_events_page(driver, timeout=20):
    """Navigate to the events confirmation page"""
    print("Navigating to events page...")
    
    wait = WebDriverWait(driver, timeout)
    
    try:
        # First, try to find and click the Events badge
        # Look for various possible selectors
        selectors_to_try = [
            "//div[contains(@class, 'v-badge') and contains(., '849')]",
            "//div[contains(@class, 'v-badge')]//span[contains(text(), '849')]/..",
            "//div[contains(@class, 'v-badge')]//span[contains(text(), '849')]/../..",
            "//div[contains(text(), 'Events')]",
            "//span[contains(text(), 'Events')]/.."
        ]
        
        clicked = False
        for selector in selectors_to_try:
            try:
                events_element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                events_element.click()
                clicked = True
                print(f"✓ Clicked events element using selector: {selector}")
                break
            except:
                continue
        
        if not clicked:
            print("✗ Could not find clickable events element")
            return False
        
        # Wait for events table to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "v-data-table")))
        print("✓ Events table loaded successfully!")
        return True
        
    except TimeoutException:
        print("✗ Could not navigate to events page - timeout")
        return False
    except Exception as e:
        print(f"✗ Could not navigate to events page: {e}")
        return False

def get_duplicate_events(driver):
    """Find all duplicate events in the current page"""
    print("Scanning for duplicate events...")
    
    duplicates = []
    
    try:
        # Find all table rows in tbody
        rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
        
        if not rows:
            print("No table rows found")
            return duplicates
        
        print(f"Found {len(rows)} events on this page")
        
        # Dictionary to track events by title, place, and time
        events_seen = {}
        
        for i, row in enumerate(rows):
            try:
                # Extract event details from each column
                cells = row.find_elements(By.XPATH, ".//td")
                
                if len(cells) < 4:
                    print(f"Row {i} doesn't have enough columns")
                    continue
                
                title = cells[0].text.strip()
                place = cells[1].text.strip() 
                when = cells[2].text.strip()
                
                # Create a unique key for the event
                event_key = f"{title}|{place}|{when}"
                
                if event_key in events_seen:
                    # This is a duplicate - find the remove button
                    try:
                        remove_button = row.find_element(By.XPATH, ".//button[contains(@class, 'error--text') and .//span[text()='Remove']]")
                        duplicates.append({
                            'row_index': i,
                            'title': title,
                            'place': place,
                            'when': when,
                            'remove_button': remove_button,
                            'event_key': event_key
                        })
                        print(f"  → Duplicate found: '{title}' at '{place}' on '{when}'")
                    except NoSuchElementException:
                        print(f"  → Duplicate found but no remove button: '{title}'")
                else:
                    events_seen[event_key] = i
                    
            except Exception as e:
                print(f"Could not parse row {i}: {e}")
                continue
                
    except Exception as e:
        print(f"Error scanning for duplicates: {e}")
    
    return duplicates

def remove_duplicate_events(driver, duplicates, max_removals=5, delay=3):
    """Remove duplicate events (with safety limit)"""
    if len(duplicates) == 0:
        print("No duplicates found on current page!")
        return 0
    
    print(f"Found {len(duplicates)} duplicate events")
    print(f"Will remove up to {max_removals} duplicates from this page")
    
    removed_count = 0
    
    for i, duplicate in enumerate(duplicates[:max_removals]):
        try:
            print(f"\n[{i+1}/{min(len(duplicates), max_removals)}] Removing: '{duplicate['title']}'")
            
            # Scroll to the element to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView(true);", duplicate['remove_button'])
            time.sleep(1)
            
            # Click the remove button
            duplicate['remove_button'].click()
            
            # Wait for any confirmation dialog
            time.sleep(2)
            
            # Look for confirmation dialog and handle it
            try:
                confirmation_selectors = [
                    "//button[contains(., 'Yes')]",
                    "//button[contains(., 'Confirm')]", 
                    "//button[contains(., 'Delete')]",
                    "//button[contains(., 'Remove')]",
                    "//button[contains(@class, 'primary')]"
                ]
                
                confirmed = False
                for selector in confirmation_selectors:
                    try:
                        confirm_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        confirm_button.click()
                        print(f"  ✓ Confirmed removal")
                        confirmed = True
                        break
                    except:
                        continue
                
                if not confirmed:
                    print("  ! No confirmation dialog found - removal may have been immediate")
                
                removed_count += 1
                
            except Exception as e:
                print(f"  ! Error with confirmation: {e}")
                removed_count += 1  # Count it anyway
            
            # Wait between removals
            if delay > 0:
                print(f"  Waiting {delay} seconds...")
                time.sleep(delay)
            
        except Exception as e:
            print(f"  ✗ Error removing duplicate: {e}")
            continue
    
    return removed_count

def process_all_pages(driver, config):
    """Process multiple pages of events"""
    total_removed = 0
    page = 1
    max_pages = config['MAX_PAGES_TO_PROCESS']
    
    print(f"\nStarting duplicate removal process (max {max_pages} pages)")
    print("=" * 50)
    
    while page <= max_pages:
        print(f"\n📄 Processing page {page}")
        
        # Get duplicates on current page
        duplicates = get_duplicate_events(driver)
        
        if len(duplicates) == 0:
            print("✓ No duplicates on this page")
        else:
            # Remove duplicates
            removed = remove_duplicate_events(
                driver, 
                duplicates, 
                max_removals=config['MAX_REMOVALS_PER_PAGE'],
                delay=config['DELAY_BETWEEN_REMOVALS']
            )
            total_removed += removed
            
            print(f"✓ Removed {removed} duplicates from page {page}")
            
            # Refresh page after removals to get updated list
            print("Refreshing page...")
            driver.refresh()
            time.sleep(5)
        
        # Try to go to next page
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next page' and not(@disabled)]"))
            )
            
            print("Going to next page...")
            next_button.click()
            time.sleep(5)
            page += 1
            
        except TimeoutException:
            print("✓ No more pages available")
            break
        except Exception as e:
            print(f"✗ Error navigating to next page: {e}")
            break
    
    return total_removed

def main():
    print("🚀 Gancio Duplicate Event Remover v3")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    print(f"Server: {config['BASE_URL']}")
    print(f"Email: {config['EMAIL']}")
    print(f"Max removals per page: {config['MAX_REMOVALS_PER_PAGE']}")
    print(f"Max pages to process: {config['MAX_PAGES_TO_PROCESS']}")
    
    # Setup WebDriver
    driver = setup_driver(headless=config['HEADLESS_MODE'])
    
    try:
        # Login
        if not login_to_gancio(driver, config['BASE_URL'], config['EMAIL'], config['PASSWORD'], config['BROWSER_TIMEOUT']):
            print("❌ Failed to login - exiting")
            return 1
        
        # Navigate to events page
        if not navigate_to_events_page(driver, config['BROWSER_TIMEOUT']):
            print("❌ Failed to navigate to events page - exiting")
            return 1
        
        # Process events across multiple pages
        total_removed = process_all_pages(driver, config)
        
        print("\n" + "=" * 50)
        print("🎉 SUMMARY")
        print(f"Total duplicate events removed: {total_removed}")
        print("=" * 50)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Script error: {e}")
        return 1
    
    finally:
        if not config['HEADLESS_MODE']:
            input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
