#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys

def setup_driver(headless=False):
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

def debug_login():
    """Debug login process step by step"""
    config = {
        'BASE_URL': 'https://orlandopunx.com',
        'EMAIL': 'godlessamericarecords@gmail.com',
        'PASSWORD': 'Marmalade-Stapling-Watch7'
    }
    
    # Try both headless and non-headless modes
    for headless_mode in [True, False]:
        print(f"\n{'='*60}")
        print(f"Testing with headless mode: {headless_mode}")
        print('='*60)
        
        driver = setup_driver(headless=headless_mode)
        
        try:
            # Step 1: Navigate to login page
            login_url = f"{config['BASE_URL']}/login"
            print(f"\n1. Navigating to: {login_url}")
            driver.get(login_url)
            
            # Wait for page load
            print("Waiting 10 seconds for page to load...")
            time.sleep(10)
            
            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
            
            # Step 2: Check page content
            page_source_sample = driver.page_source[:500]
            print(f"Page source sample: {page_source_sample}")
            
            # Step 3: Look for input fields
            print("\n2. Looking for input fields...")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"Found {len(inputs)} input elements:")
            
            for i, inp in enumerate(inputs):
                try:
                    input_type = inp.get_attribute("type") or "text"
                    input_id = inp.get_attribute("id") or "no-id"
                    input_name = inp.get_attribute("name") or "no-name"
                    input_placeholder = inp.get_attribute("placeholder") or "no-placeholder"
                    print(f"  Input {i}: type='{input_type}', id='{input_id}', name='{input_name}', placeholder='{input_placeholder}'")
                except Exception as e:
                    print(f"  Input {i}: Error getting attributes - {e}")
            
            # Step 4: Look for buttons
            print("\n3. Looking for buttons...")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} button elements:")
            
            for i, btn in enumerate(buttons):
                try:
                    btn_text = btn.text.strip()
                    btn_type = btn.get_attribute("type") or "button"
                    print(f"  Button {i}: text='{btn_text}', type='{btn_type}'")
                except Exception as e:
                    print(f"  Button {i}: Error getting attributes - {e}")
            
            # Step 5: Try to find email field specifically
            print("\n4. Trying to find email field...")
            email_field = None
            email_selectors = [
                (By.ID, "input-45"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.XPATH, "//input[@type='email']")
            ]
            
            for by, selector in email_selectors:
                try:
                    email_field = driver.find_element(by, selector)
                    print(f"✓ Found email field using: {by} = {selector}")
                    break
                except:
                    print(f"✗ Could not find email field using: {by} = {selector}")
            
            if email_field:
                print("✓ Email field found! Attempting login...")
                
                # Try to fill the form
                email_field.clear()
                email_field.send_keys(config['EMAIL'])
                print("✓ Email entered")
                
                # Find password field
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    password_field.clear()
                    password_field.send_keys(config['PASSWORD'])
                    print("✓ Password entered")
                    
                    # Find login button
                    try:
                        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
                        print("✓ Found login button, clicking...")
                        login_button.click()
                        
                        # Wait for result
                        print("Waiting 10 seconds for login to complete...")
                        time.sleep(10)
                        
                        print(f"After login - URL: {driver.current_url}")
                        print(f"After login - Title: {driver.title}")
                        
                        # Check for admin elements
                        badges = driver.find_elements(By.XPATH, "//div[contains(@class, 'v-badge')]")
                        if badges:
                            print(f"✓ Found {len(badges)} badge elements - login successful!")
                        else:
                            print("✗ No badge elements found")
                            
                    except Exception as e:
                        print(f"✗ Could not find/click login button: {e}")
                        
                except Exception as e:
                    print(f"✗ Could not find password field: {e}")
                    
            else:
                print("✗ No email field found")
                print("Full page source:")
                print(driver.page_source)
            
            # If non-headless mode, ask user to continue
            if not headless_mode:
                input("Press Enter to continue to next test or close browser...")
                
        except Exception as e:
            print(f"Error during test: {e}")
        
        finally:
            driver.quit()
            print(f"Closed browser for headless={headless_mode}")

if __name__ == "__main__":
    debug_login()
