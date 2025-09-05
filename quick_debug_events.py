#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

def quick_debug():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Login
        driver.get("https://orlandopunx.com/login")
        time.sleep(5)
        
        email_field = driver.find_element(By.ID, "input-45")
        email_field.send_keys("godlessamericarecords@gmail.com")
        
        password_field = driver.find_element(By.ID, "input-48")
        password_field.send_keys("Marmalade-Stapling-Watch7")
        
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        time.sleep(8)
        
        # Go to admin
        driver.get("https://orlandopunx.com/admin")
        time.sleep(5)
        
        # Save "before click" state
        with open("admin_before_click.html", "w") as f:
            f.write(driver.page_source)
        print("💾 Saved admin_before_click.html")
        
        # Click Events
        events_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Events')]")
        print(f"Found Events element: '{events_element.text.strip()}'")
        events_element.click()
        
        # Wait a bit and save "after click" state
        time.sleep(10)
        
        with open("admin_after_click.html", "w") as f:
            f.write(driver.page_source)
        print("💾 Saved admin_after_click.html")
        
        # Quick check for tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
        print(f"Found {len(tables)} tables and {len(rows)} data rows")
        
        print(f"Current URL: {driver.current_url}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    quick_debug()
