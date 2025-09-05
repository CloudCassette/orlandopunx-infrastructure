#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

def setup_driver():
    """Setup Chrome WebDriver with appropriate options"""
    options = Options()
    # Remove headless mode to see what's happening
    # options.add_argument("--headless")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def login_to_gancio(driver, base_url, email, password):
    """Login to Gancio admin interface"""
    print("Logging in to Gancio...")
    
    login_url = f"{base_url}/login"
    driver.get(login_url)
    
    # Wait for login form to load
    wait = WebDriverWait(driver, 20)
    
    try:
        # Find email field (using ID from previous session)
        email_field = wait.until(EC.presence_of_element_located((By.ID, "input-45")))
        email_field.send_keys(email)
        
        # Find password field
        password_field = driver.find_element(By.ID, "input-48")
        password_field.send_keys(password)
        
        # Find and click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        login_button.click()
        
        # Wait for admin page to load
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'v-badge')]")))
        print("Login successful!")
        
    except TimeoutException:
        print("Login failed - timeout waiting for elements")
        return False
    
    return True

def navigate_to_events_page(driver):
    """Navigate to the events confirmation page"""
    print("Navigating to events page...")
    
    # Click on the Events badge/tab
    wait = WebDriverWait(driver, 10)
    
    try:
        # Look for the Events badge or related clickable element
        events_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'v-badge') and .//span[text()='849']]/..")))
        events_element.click()
        
        # Wait for events table to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "v-data-table")))
        print("Events page loaded successfully!")
        
    except TimeoutException:
        print("Could not navigate to events page")
        return False
    
    return True

def get_duplicate_events(driver):
    """Find all duplicate events in the current page"""
    print("Scanning for duplicate events...")
    
    duplicates = []
    
    try:
        # Find all table rows
        rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
        
        # Dictionary to track events by title and details
        events_seen = {}
        
        for i, row in enumerate(rows):
            try:
                # Extract event details
                title_cell = row.find_element(By.XPATH, ".//td[1]")
                place_cell = row.find_element(By.XPATH, ".//td[2]")
                when_cell = row.find_element(By.XPATH, ".//td[3]")
                
                title = title_cell.text.strip()
                place = place_cell.text.strip()
                when = when_cell.text.strip()
                
                # Create a unique key for the event
                event_key = f"{title}|{place}|{when}"
                
                if event_key in events_seen:
                    # This is a duplicate
                    remove_button = row.find_element(By.XPATH, ".//button[contains(@class, 'error--text') and .//span[text()='Remove']]")
                    duplicates.append({
                        'row_index': i,
                        'title': title,
                        'place': place,
                        'when': when,
                        'remove_button': remove_button
                    })
                    print(f"Found duplicate: {title} at {place} on {when}")
                else:
                    events_seen[event_key] = i
                    
            except NoSuchElementException:
                print(f"Could not parse row {i}")
                continue
                
    except Exception as e:
        print(f"Error scanning for duplicates: {e}")
    
    return duplicates

def remove_duplicate_events(driver, duplicates, max_removals=5):
    """Remove duplicate events (with safety limit)"""
    print(f"Found {len(duplicates)} duplicate events")
    
    if len(duplicates) == 0:
        print("No duplicates found on current page!")
        return 0
    
    removed_count = 0
    
    for i, duplicate in enumerate(duplicates[:max_removals]):
        try:
            print(f"Removing duplicate {i+1}/{min(len(duplicates), max_removals)}: {duplicate['title']}")
            
            # Click the remove button
            duplicate['remove_button'].click()
            
            # Wait for any confirmation dialog and handle it
            time.sleep(2)
            
            # Look for confirmation dialog
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Yes') or contains(., 'Confirm') or contains(., 'Delete')]"))
                )
                confirm_button.click()
                print(f"Confirmed removal of: {duplicate['title']}")
                removed_count += 1
                
            except TimeoutException:
                print("No confirmation dialog found, removal may have been immediate")
                removed_count += 1
            
            # Wait a moment between removals
            time.sleep(3)
            
        except Exception as e:
            print(f"Error removing duplicate: {e}")
            continue
    
    return removed_count

def process_all_pages(driver, max_pages=10):
    """Process multiple pages of events"""
    total_removed = 0
    page = 1
    
    while page <= max_pages:
        print(f"\n--- Processing page {page} ---")
        
        # Get duplicates on current page
        duplicates = get_duplicate_events(driver)
        
        if len(duplicates) == 0:
            print("No duplicates on this page")
        else:
            # Remove duplicates (limit to 5 per page for safety)
            removed = remove_duplicate_events(driver, duplicates, max_removals=5)
            total_removed += removed
            
            # Refresh page after removals
            driver.refresh()
            time.sleep(5)
        
        # Try to go to next page
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next page' and not(@disabled)]"))
            )
            next_button.click()
            time.sleep(5)
            page += 1
            
        except TimeoutException:
            print("No more pages or next button not available")
            break
    
    return total_removed

def main():
    # Configuration - UPDATE THESE VALUES
    BASE_URL = "http://localhost:3000"  # Update with your Gancio URL
    EMAIL = "your-email@example.com"    # Update with your email
    PASSWORD = "your-password"           # Update with your password
    
    driver = setup_driver()
    
    try:
        # Login
        if not login_to_gancio(driver, BASE_URL, EMAIL, PASSWORD):
            print("Failed to login")
            return
        
        # Navigate to events page
        if not navigate_to_events_page(driver):
            print("Failed to navigate to events page")
            return
        
        # Process events across multiple pages
        total_removed = process_all_pages(driver, max_pages=10)
        
        print(f"\n=== Summary ===")
        print(f"Total duplicate events removed: {total_removed}")
        
    except Exception as e:
        print(f"Script error: {e}")
    
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
