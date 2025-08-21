#!/usr/bin/env python3
"""
🔍 Check Gancio Admin Panel (Fixed)
===================================
Investigates the admin panel to see submitted events using correct login method
"""

import requests
import json
import os
import getpass
from datetime import datetime

def check_gancio_admin():
    """Check admin panel for events"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Use existing credentials
    email = "godlessamericarecords@gmail.com"
    password = os.environ.get('GANCIO_PASSWORD')
    
    if not password:
        print("🔑 Enter Gancio password:")
        password = getpass.getpass()
    
    print(f"🔍 Checking Gancio admin panel...")
    
    # Login using the working method
    login_url = "https://orlandopunx.com/login"
    login_data = {"email": email, "password": password}
    
    try:
        response = session.post(login_url, data=login_data, allow_redirects=True)
        print(f"🔐 Login response: {response.status_code}")
        print(f"🔗 Final URL: {response.url}")
        
        if response.status_code == 200 and 'admin' in response.url:
            print("✅ Login successful!")
            
            # Try different admin endpoints
            endpoints_to_try = [
                "/api/admin/events",
                "/api/events?admin=true", 
                "/admin/api/events",
                "/api/events"
            ]
            
            for endpoint in endpoints_to_try:
                admin_events_url = f"https://orlandopunx.com{endpoint}"
                print(f"\n🔍 Trying: {endpoint}")
                events_response = session.get(admin_events_url)
                print(f"📋 Response: {events_response.status_code}")
                
                if events_response.status_code == 200:
                    try:
                        events_data = events_response.json()
                        print(f"📊 Found {len(events_data)} events")
                        
                        # Look for Conduit events
                        conduit_events = []
                        recent_events = []
                        
                        for event in events_data:
                            # Check if it's a Conduit event
                            place_id = event.get('place_id') or event.get('place', {}).get('id')
                            place_name = event.get('place', {}).get('name', '')
                            
                            if place_id == 3 or 'conduit' in place_name.lower():
                                conduit_events.append(event)
                            
                            # Collect recent events
                            created_at = event.get('created_at', event.get('createdAt', ''))
                            if created_at and created_at.startswith('2025-08-19'):
                                recent_events.append(event)
                        
                        print(f"🎸 Conduit events (place_id=3): {len(conduit_events)}")
                        print(f"📅 Today's events: {len(recent_events)}")
                        
                        if conduit_events:
                            print("\n✅ CONDUIT EVENTS FOUND:")
                            for event in conduit_events[:5]:
                                title = event.get('title', 'No title')[:50]
                                status = event.get('status', 'unknown')
                                print(f"   • {title} | Status: {status}")
                        
                        if recent_events:
                            print(f"\n📋 Today's submitted events:")
                            for event in recent_events[:5]:
                                title = event.get('title', 'No title')[:50]
                                place_name = event.get('place', {}).get('name', 'No venue')
                                status = event.get('status', 'unknown')
                                place_id = event.get('place_id') or event.get('place', {}).get('id', 'unknown')
                                print(f"   • {title} | {place_name} (ID:{place_id}) | {status}")
                        
                        break  # Found working endpoint
                        
                    except json.JSONDecodeError:
                        print(f"❌ Invalid JSON response")
                        print(f"Response preview: {events_response.text[:200]}")
                else:
                    print(f"❌ Failed: {events_response.text[:100]}")
            
            # Check venues with correct method
            print(f"\n🏢 Checking venues...")
            places_endpoints = ["/api/admin/places", "/api/places", "/admin/api/places"]
            
            for endpoint in places_endpoints:
                places_url = f"https://orlandopunx.com{endpoint}"
                print(f"🔍 Trying: {endpoint}")
                places_response = session.get(places_url)
                print(f"📍 Response: {places_response.status_code}")
                
                if places_response.status_code == 200:
                    try:
                        places_data = places_response.json()
                        print(f"📍 Found {len(places_data)} venues")
                        
                        print(f"\n🏢 All venues:")
                        for place in places_data:
                            place_id = place.get('id')
                            name = place.get('name', 'No name')
                            address = place.get('address', 'No address')[:50]
                            print(f"   • ID {place_id}: {name} - {address}")
                        
                        break
                    except json.JSONDecodeError:
                        print(f"❌ Invalid JSON response")
                        
        elif response.status_code == 200:
            print("✅ Login succeeded but no admin redirect")
            print(f"📋 Response preview: {response.text[:300]}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_gancio_admin()
