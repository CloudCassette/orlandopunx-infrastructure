#!/usr/bin/env python3
"""
Explore Gancio page source to understand the structure
"""

import os
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re

def explore_gancio_pages():
    print("🔍 EXPLORING GANCIO PAGE STRUCTURE")
    print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Explore login page
        print("\n📋 EXPLORING LOGIN PAGE")
        print("-" * 30)
        
        driver.get("http://localhost:13120/login")
        
        # Get page source
        source = driver.page_source
        
        print("📄 Login Page Source Analysis:")
        print(f"   Page length: {len(source)} characters")
        
        # Look for form elements
        print("\n🔍 Form elements found:")
        
        # Look for input elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   Total input elements: {len(inputs)}")
        
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_class = inp.get_attribute("class")
            input_placeholder = inp.get_attribute("placeholder")
            
            print(f"   Input {i+1}: type='{input_type}', name='{input_name}', id='{input_id}', class='{input_class}', placeholder='{input_placeholder}'")
        
        # Look for form elements specifically
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"\n📝 Form elements: {len(forms)}")
        
        for i, form in enumerate(forms):
            action = form.get_attribute("action")
            method = form.get_attribute("method")
            print(f"   Form {i+1}: action='{action}', method='{method}'")
            
            # Find inputs within this form
            form_inputs = form.find_elements(By.TAG_NAME, "input")
            for j, inp in enumerate(form_inputs):
                input_type = inp.get_attribute("type")
                input_name = inp.get_attribute("name")
                print(f"     Input {j+1}: type='{input_type}', name='{input_name}'")
        
        # Look for buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n🔘 Button elements: {len(buttons)}")
        
        for i, btn in enumerate(buttons):
            btn_type = btn.get_attribute("type")
            btn_text = btn.text
            btn_onclick = btn.get_attribute("onclick")
            print(f"   Button {i+1}: type='{btn_type}', text='{btn_text}', onclick='{btn_onclick}'")
        
        # Search for email/password patterns in source
        print("\n🔍 Searching for email/password patterns in source:")
        
        email_patterns = [
            r'email', r'Email', r'EMAIL',
            r'user', r'User', r'username',
            r'login', r'Login'
        ]
        
        password_patterns = [
            r'password', r'Password', r'PASSWORD',
            r'pass', r'Pass'
        ]
        
        for pattern in email_patterns:
            matches = re.findall(f'[^>]*{pattern}[^<]*', source, re.IGNORECASE)
            if matches:
                print(f"   Email pattern '{pattern}': {len(matches)} matches")
                for match in matches[:3]:  # Show first 3
                    clean_match = re.sub(r'<[^>]*>', '', match).strip()
                    if clean_match:
                        print(f"     {clean_match[:60]}...")
        
        # Try alternative selectors
        print("\n🎯 Testing alternative selectors:")
        
        selectors_to_test = [
            ("input[type='email']", "email input"),
            ("input[type='text']", "text input"),
            ("input[placeholder*='email']", "email placeholder"),
            ("input[placeholder*='Email']", "Email placeholder"),
            ("#email", "email ID"),
            ("#Email", "Email ID"),
            (".email", "email class"),
            ("input[name*='email']", "email name contains"),
            ("input[id*='email']", "email id contains"),
        ]
        
        for selector, description in selectors_to_test:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ {description}: Found {len(elements)} elements")
                    for elem in elements[:2]:
                        name = elem.get_attribute("name")
                        elem_id = elem.get_attribute("id")
                        print(f"      name='{name}', id='{elem_id}'")
                else:
                    print(f"   ❌ {description}: No elements found")
            except Exception as e:
                print(f"   ❌ {description}: Error - {e}")
        
        # Check if page is using JavaScript for forms
        print("\n⚙️ JavaScript analysis:")
        script_tags = driver.find_elements(By.TAG_NAME, "script")
        print(f"   Found {len(script_tags)} script tags")
        
        js_content = ""
        for script in script_tags:
            script_content = script.get_attribute("innerHTML")
            if script_content:
                js_content += script_content
        
        if "vue" in js_content.lower() or "react" in js_content.lower() or "angular" in js_content.lower():
            print("   ⚡ Detected JavaScript framework - form might be dynamically generated")
        
        if "login" in js_content.lower():
            print("   🔑 Found login-related JavaScript")
        
        print(f"\n📄 Saving full page source to /tmp/gancio_login_source.html")
        with open("/tmp/gancio_login_source.html", "w") as f:
            f.write(source)
        
        # Try to explore what happens after any potential redirects
        print("\n🏠 Exploring main page after potential login redirect:")
        driver.get("http://localhost:13120/")
        
        # Look for admin-related links
        admin_patterns = ["admin", "Admin", "manage", "Manage", "settings", "Settings"]
        
        for pattern in admin_patterns:
            links = driver.find_elements(By.PARTIAL_LINK_TEXT, pattern)
            if links:
                print(f"   Found {len(links)} links containing '{pattern}'")
                for link in links[:2]:
                    href = link.get_attribute("href")
                    text = link.text
                    print(f"     {text}: {href}")
        
    except Exception as e:
        print(f"❌ Error exploring pages: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    explore_gancio_pages()
