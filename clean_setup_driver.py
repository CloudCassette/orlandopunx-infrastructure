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
