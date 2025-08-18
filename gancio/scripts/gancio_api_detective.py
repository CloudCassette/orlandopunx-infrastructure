#!/usr/bin/env python3
"""
Gancio API Detective - Figure out the exact API format for event creation
"""

import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import getpass

class GancioAPIDetective:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        self.authenticated = False
    
    def authenticate(self):
        """Try to authenticate with session-based login"""
        print("🔑 Setting up authentication...")
        
        email = input("Enter your Gancio email: ").strip()
        if not email:
            return False
            
        password = getpass.getpass("Enter your password: ").strip()
        if not password:
            return False
        
        try:
            # Form-based login that we know works
            login_data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Authentication successful")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_comprehensive_api(self):
        """Test all possible API formats and endpoints"""
        print("\n🕵️  Starting comprehensive API detection...")
        
        # Create test event data
        now = datetime.now()
        start_time = now + timedelta(hours=1)
        end_time = start_time + timedelta(hours=3)
        
        # Test with real event data from our scraping
        test_events = [
            {
                "title": "API Test Event (Will Delete)",
                "start_datetime": int(start_time.timestamp()),
                "end_datetime": int(end_time.timestamp()),
                "description": "Test event - please ignore and delete",
                "tags": ["test"],
                "place": {"name": "Test Venue", "address": "123 Test St"}
            },
            {
                "title": "API Test Event (Will Delete)",
                "start_datetime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_datetime": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "description": "Test event - please ignore and delete",
                "tags": ["test"],
                "place": {"name": "Test Venue", "address": "123 Test St"}
            },
            {
                "title": "API Test Event (Will Delete)",
                "start_datetime": start_time.isoformat(),
                "end_datetime": end_time.isoformat(),
                "description": "Test event - please ignore and delete",
                "tags": ["test"],
                "place_name": "Test Venue"
            },
            # Minimal version
            {
                "title": "API Test Event (Will Delete)",
                "start_datetime": int(start_time.timestamp()),
                "description": "Test event - please ignore and delete"
            },
            # Form-style data
            {
                "title": "API Test Event (Will Delete)",
                "start_datetime": int(start_time.timestamp()),
                "end_datetime": int(end_time.timestamp()),
                "description": "Test event - please ignore and delete",
                "tags": "test",
                "place": "Test Venue"
            }
        ]
        
        # Test different endpoints
        endpoints = [
            "/api/event",
            "/api/events", 
            "/event",
            "/events",
            "/add",
            "/admin/api/event",
            "/admin/api/events",
            "/admin/event",
            "/admin/events"
        ]
        
        # Test different content types and methods
        test_configs = [
            {"content_type": "application/json", "method": "POST"},
            {"content_type": "application/x-www-form-urlencoded", "method": "POST"},
            {"content_type": "multipart/form-data", "method": "POST"}
        ]
        
        successful_calls = []
        
        for i, event_data in enumerate(test_events, 1):
            print(f"\n📊 Testing event format {i}/{len(test_events)}")
            print(f"   Data preview: {str(event_data)[:100]}...")
            
            for endpoint in endpoints:
                for config in test_configs:
                    full_url = f"{self.base_url}{endpoint}"
                    
                    try:
                        # Set headers
                        headers = {'Content-Type': config['content_type']}
                        
                        # Send request based on content type
                        if config['content_type'] == 'application/json':
                            response = self.session.post(full_url, json=event_data, headers=headers, timeout=10)
                        elif config['content_type'] == 'application/x-www-form-urlencoded':
                            # Flatten nested objects for form data
                            form_data = self.flatten_dict(event_data)
                            response = self.session.post(full_url, data=form_data, timeout=10)
                        else:
                            # Skip multipart for now
                            continue
                        
                        # Check response
                        if response.status_code in [200, 201]:
                            print(f"🎉 SUCCESS! {config['method']} {endpoint} with {config['content_type']}")
                            print(f"   Response: {response.text[:200]}")
                            
                            # Try to find the created event
                            try:
                                response_data = response.json() if response.text.strip() else {}
                                if 'id' in response_data:
                                    print(f"   Created event ID: {response_data['id']}")
                                    
                                    # Try to delete it
                                    delete_response = self.session.delete(f"{full_url}/{response_data['id']}")
                                    if delete_response.status_code in [200, 204]:
                                        print("   🗑️  Test event deleted successfully")
                                    
                            except:
                                pass
                            
                            successful_calls.append({
                                'endpoint': endpoint,
                                'method': config['method'],
                                'content_type': config['content_type'],
                                'event_format': i,
                                'response_code': response.status_code,
                                'response': response.text[:200]
                            })
                            
                            # Found a working method!
                            return successful_calls
                        
                        elif response.status_code == 400:
                            # Bad request might mean wrong format, but endpoint exists
                            if endpoint == "/api/event":
                                print(f"   💡 {endpoint} exists but data format wrong: {response.text[:50]}")
                        
                        elif response.status_code not in [404, 405]:
                            # Other interesting responses
                            print(f"   🔍 {endpoint} ({config['content_type']}): {response.status_code}")
                            if response.text.strip() and len(response.text) < 200:
                                print(f"      Response: {response.text}")
                    
                    except Exception as e:
                        # Skip connection errors etc
                        pass
        
        return successful_calls
    
    def flatten_dict(self, d, parent_key='', sep='_'):
        """Flatten nested dictionary for form data"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, ','.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def test_places_api(self):
        """Test if we need to create places first"""
        print("\n📍 Testing places API...")
        
        endpoints = ["/api/places", "/api/place", "/places", "/place"]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ Found places endpoint: {endpoint}")
                    try:
                        places = response.json()
                        print(f"   Places: {places}")
                        return endpoint, places
                    except:
                        pass
            except:
                pass
        
        print("❌ No places endpoint found")
        return None, []
    
    def analyze_existing_events(self):
        """Look at existing events to understand the data structure"""
        print("\n🔍 Analyzing existing event structure...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                if events:
                    event = events[0]
                    print("✅ Event structure analysis:")
                    print(f"   Fields: {list(event.keys())}")
                    print(f"   Sample: {json.dumps(event, indent=2)[:300]}...")
                    return event
        except Exception as e:
            print(f"❌ Could not analyze events: {e}")
        
        return None
    
    def run_detection(self):
        """Main detection process"""
        print("🕵️  Gancio API Detective Starting...")
        print("="*50)
        
        # Step 1: Analyze existing structure
        sample_event = self.analyze_existing_events()
        
        # Step 2: Check places API
        places_endpoint, places = self.test_places_api()
        
        # Step 3: Try authentication
        if not self.authenticated:
            print("\n🔑 Authentication may be needed for event creation...")
            auth_success = self.authenticate()
            if not auth_success:
                print("⚠️  Continuing without authentication...")
        
        # Step 4: Comprehensive API testing
        successful_calls = self.test_comprehensive_api()
        
        # Results
        print("\n" + "="*50)
        print("🎯 DETECTION RESULTS:")
        print("="*50)
        
        if successful_calls:
            print("✅ FOUND WORKING API METHODS:")
            for call in successful_calls:
                print(f"   • {call['method']} {call['endpoint']} ({call['content_type']})")
                print(f"     Event format: {call['event_format']}, Response: {call['response_code']}")
        else:
            print("❌ No working API methods found")
            print("\nPossible solutions:")
            print("   1. Check if anonymous event creation is actually enabled in admin")
            print("   2. The API might use a different authentication method") 
            print("   3. The event data structure might be different than expected")
            print("   4. Events might need to be approved before appearing")
        
        # Additional info
        if sample_event:
            print(f"\n📋 Use this structure for events:")
            print(f"   Required fields: title, start_datetime, description")
            if 'placeId' in sample_event:
                print(f"   Place format: Use placeId instead of place object")
            
        return successful_calls

if __name__ == "__main__":
    detective = GancioAPIDetective("https://orlandopunx.com")
    results = detective.run_detection()
