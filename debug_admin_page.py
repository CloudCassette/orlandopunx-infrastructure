#!/usr/bin/env python3

import requests
import re

def test_admin_access():
    session = requests.Session()
    
    # Login
    login_data = {
        'email': 'admin',
        'password': 'OrlandoPunkShows2024!'
    }
    
    login_response = session.post("https://orlandopunx.com/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    # Get admin page
    admin_response = session.get("https://orlandopunx.com/admin")
    print(f"Admin page status: {admin_response.status_code}")
    print(f"Admin page length: {len(admin_response.text)}")
    
    # Check for events data
    if 'unconfirmedEvents' in admin_response.text:
        print("✅ Found unconfirmedEvents in admin page")
        
        # Extract events
        pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
        matches = re.findall(pattern, admin_response.text)
        print(f"Found {len(matches)} events via regex")
        
        # Show first few
        for i, match in enumerate(matches[:5]):
            event_id, title_var, slug = match
            print(f"  {i+1}. ID: {event_id}, Slug: {slug}")
            
    else:
        print("❌ No unconfirmedEvents found")
        
        # Look for other event indicators
        if 'Events' in admin_response.text:
            print("Found 'Events' text")
        if 'window.__NUXT__' in admin_response.text:
            print("Found __NUXT__ data")
            
        # Save a sample to check
        with open('debug_admin.html', 'w') as f:
            f.write(admin_response.text)
        print("Saved admin page to debug_admin.html")

if __name__ == "__main__":
    test_admin_access()
