def login_to_gancio(driver, base_url, email, password, timeout=30):
    """Login to Gancio admin interface with improved error handling"""
    print("Logging in to Gancio...")
    
    login_url = f"{base_url}/login"
    print(f"Navigating to: {login_url}")
    driver.get(login_url)
    
    # Wait longer for the page to load
    time.sleep(5)
    
    wait = WebDriverWait(driver, timeout)
    
    try:
        print("Looking for login form...")
        
        # Try multiple selectors for email field
        email_field = None
        email_selectors = [
            (By.ID, "input-45"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.XPATH, "//input[@type='email']"),
            (By.XPATH, "//input[contains(@placeholder, 'mail') or contains(@placeholder, 'Email')]")
        ]
        
        for by, selector in email_selectors:
            try:
                email_field = wait.until(EC.presence_of_element_located((by, selector)))
                print(f"✓ Found email field using: {by} = {selector}")
                break
            except TimeoutException:
                continue
        
        if not email_field:
            print("✗ Could not find email field")
            print("Page source (first 2000 chars):")
            print(driver.page_source[:2000])
            return False
        
        # Clear and enter email
        email_field.clear()
        email_field.send_keys(email)
        print("✓ Email entered")
        
        # Try multiple selectors for password field
        password_field = None
        password_selectors = [
            (By.ID, "input-48"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.XPATH, "//input[@type='password']")
        ]
        
        for by, selector in password_selectors:
            try:
                password_field = driver.find_element(by, selector)
                print(f"✓ Found password field using: {by} = {selector}")
                break
            except:
                continue
        
        if not password_field:
            print("✗ Could not find password field")
            return False
        
        # Clear and enter password
        password_field.clear()
        password_field.send_keys(password)
        print("✓ Password entered")
        
        # Try multiple selectors for login button
        login_button = None
        button_selectors = [
            (By.XPATH, "//button[contains(., 'Login')]"),
            (By.XPATH, "//button[contains(., 'Sign')]"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']")
        ]
        
        for by, selector in button_selectors:
            try:
                login_button = driver.find_element(by, selector)
                print(f"✓ Found login button using: {by} = {selector}")
                break
            except:
                continue
        
        if not login_button:
            print("✗ Could not find login button")
            return False
        
        # Click login button
        print("Clicking login button...")
        login_button.click()
        
        # Wait longer for redirect and admin page to load
        print("Waiting for login to complete...")
        time.sleep(8)
        
        # Check multiple indicators of successful login
        success_indicators = [
            (By.XPATH, "//div[contains(@class, 'v-badge')]"),
            (By.XPATH, "//span[contains(text(), 'Events')]"),
            (By.XPATH, "//div[contains(@class, 'v-tab')]"),
            (By.CSS_SELECTOR, ".v-badge"),
            (By.XPATH, "//div[contains(text(), 'admin') or contains(text(), 'Admin')]")
        ]
        
        login_successful = False
        for by, selector in success_indicators:
            try:
                elements = driver.find_elements(by, selector)
                if elements:
                    print(f"✓ Login successful! Found indicator: {by} = {selector} ({len(elements)} elements)")
                    login_successful = True
                    break
            except:
                continue
        
        if not login_successful:
            print("✗ Login may have failed - no admin indicators found")
            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
            
            # Check if we're still on login page or got redirected
            if "login" in driver.current_url.lower():
                print("Still on login page - credentials may be incorrect")
            else:
                print("Redirected but no admin interface found")
            
            # Print some page content for debugging
            print("Page source (first 1000 chars):")
            print(driver.page_source[:1000])
            return False
        
        print("✓ Login successful!")
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
