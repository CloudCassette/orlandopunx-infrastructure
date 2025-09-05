import tempfile
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def setup_driver_fixed(headless=False):
    """Setup Chrome WebDriver with unique user data directory"""
    # Create a unique temporary directory for this session
    temp_dir = tempfile.mkdtemp(prefix="gancio_chrome_")
    
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    # Essential Chrome options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Use unique user data directory
    options.add_argument(f"--user-data-dir={temp_dir}")
    
    # Additional options to avoid conflicts
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--remote-debugging-port=0")  # Use random available port
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        print(f"✓ Chrome started with temp directory: {temp_dir}")
        return driver
    except Exception as e:
        print(f"ERROR: Could not start Chrome WebDriver: {e}")
        # Clean up temp directory if driver creation failed
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

# Test the fixed driver setup
if __name__ == "__main__":
    print("Testing Chrome WebDriver setup...")
    try:
        driver = setup_driver_fixed()
        print("✓ Chrome WebDriver started successfully!")
        driver.quit()
        print("✓ Chrome WebDriver closed successfully!")
    except Exception as e:
        print(f"✗ Failed to start Chrome WebDriver: {e}")
