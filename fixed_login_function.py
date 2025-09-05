def login_to_gancio(driver, base_url, email, password, timeout=30):
    """Login to Gancio admin interface with improved navigation"""
    print("Logging in to Gancio...")
    
    login_url = f"{base_url}/login"
    print(f"Navigating to: {login_url}")
    driver.get(login_url)
    
    # Wait for the page to load
    time.sleep(5)
    
    wait = WebDriverWait(driver, timeout)
    
    try:
        print("Looking for login form...")
        
        # Find email field
        email_field = wait.until(EC.presence_of_element_located((By.ID, "input-45")))
        print("✓ Found email field")
        
        # Clear and enter email
        email_field.clear()
        email_field.send_keys(email)
        print("✓ Email entered")
        
        # Find password field
        password_field = driver.find_element(By.ID, "input-48")
        password_field.clear()
        password_field.send_keys(password)
        print("✓ Password entered")
        
        # Find and click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'LOGIN')]")
        print("Clicking login button...")
        login_button.click()
        
        # Wait for redirect
        print("Waiting for login to complete...")
        time.sleep(8)
        
        # Check if we're redirected (not on login page anymore)
        current_url = driver.current_url
        if "login" in current_url.lower():
            print("✗ Still on login page - credentials may be incorrect")
            return False
        
        print(f"✓ Redirected to: {current_url}")
        
        # Now navigate to admin page
        admin_url = f"{base_url}/admin"
        print(f"Navigating to admin page: {admin_url}")
        driver.get(admin_url)
        
        # Wait for admin page to load
        time.sleep(5)
        
        # Check for admin interface elements
        print("Checking for admin interface...")
        admin_indicators = [
            (By.XPATH, "//div[contains(@class, 'v-badge')]"),
            (By.XPATH, "//span[contains(text(), 'Events')]"),
            (By.XPATH, "//div[contains(@class, 'v-tab')]")
        ]
        
        admin_found = False
        for by, selector in admin_indicators:
            try:
                elements = driver.find_elements(by, selector)
                if elements:
                    print(f"✓ Found admin indicator: {selector} ({len(elements)} elements)")
                    admin_found = True
                    break
            except:
                continue
        
        if not admin_found:
            print("✗ No admin indicators found")
            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
            return False
        
        print("✓ Successfully logged in and navigated to admin interface!")
        return True
        
    except TimeoutException:
        print("✗ Login failed - timeout waiting for elements")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        return False
    except Exception as e:
        print(f"✗ Login failed: {e}")
        print(f"Current URL: {driver.current_url}")
        return False
