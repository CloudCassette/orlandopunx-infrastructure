from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_chrome():
    """Test basic Chrome startup without any user data directory"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # Start in headless mode to avoid display issues
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✓ Chrome started successfully!")
        driver.get("https://www.google.com")
        print(f"✓ Page title: {driver.title}")
        driver.quit()
        print("✓ Chrome closed successfully!")
        return True
    except Exception as e:
        print(f"✗ Chrome test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing basic Chrome WebDriver functionality...")
    test_chrome()
