#!/usr/bin/env python3
"""
Deep Investigation of Gancio API for Image Upload
"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

class GancioAPIInvestigator:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

    def authenticate(self):
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        try:
            login_data = {'email': email, 'password': password}
            resp = self.session.post(f"{self.gancio_base_url}/login", data=login_data)
            return resp.status_code == 200
        except:
            return False

    def test_api_endpoints(self):
        """Test various API endpoints that might handle images"""
        print("🔍 Testing API Endpoints...")
        
        endpoints_to_test = [
            "/api",
            "/api/events",
            "/api/media",
            "/api/upload",
            "/api/files",
            "/api/images",
            "/upload",
            "/media",
            "/files",
            "/api/event/upload",
            "/api/event/media",
            "/admin/api",
            "/admin/upload"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                # Test GET
                resp = self.session.get(f"{self.gancio_base_url}{endpoint}")
                print(f"GET  {endpoint}: {resp.status_code}")
                
                if resp.status_code == 200:
                    try:
                        content = resp.json()
                        if isinstance(content, list):
                            print(f"     → Returns list with {len(content)} items")
                        elif isinstance(content, dict):
                            print(f"     → Returns dict with keys: {list(content.keys())[:5]}")
                    except:
                        print(f"     → Returns text content ({len(resp.text)} chars)")
                
                # Test POST with minimal data
                resp = self.session.post(f"{self.gancio_base_url}{endpoint}")
                if resp.status_code != 404:
                    print(f"POST {endpoint}: {resp.status_code}")
                    
            except Exception as e:
                print(f"     ERROR: {e}")

    def investigate_existing_events(self):
        """Look for any events that have images to understand the structure"""
        print("\n🔍 Investigating Existing Events...")
        
        try:
            resp = self.session.get(f"{self.gancio_base_url}/api/events")
            if resp.status_code == 200:
                events = resp.json()
                print(f"Found {len(events)} events")
                
                for i, event in enumerate(events[:5]):  # Check first 5 events
                    print(f"\nEvent {i+1}: {event.get('title', 'No title')[:50]}")
                    
                    # Look for image-related fields
                    image_fields = ['image', 'media', 'flyer', 'poster', 'picture', 'photo']
                    for field in image_fields:
                        if field in event:
                            print(f"  ✅ {field}: {event[field]}")
                    
                    # Show all fields for the first event
                    if i == 0:
                        print(f"  All fields: {list(event.keys())}")
                        
        except Exception as e:
            print(f"Error: {e}")

    def test_image_upload_methods(self):
        """Test different image upload approaches"""
        print("\n🖼️  Testing Image Upload Methods...")
        
        # Find a test image
        flyer_dir = "flyers"
        if not os.path.exists(flyer_dir):
            print("❌ No flyers directory found")
            return
            
        flyers = [f for f in os.listdir(flyer_dir) if f.endswith('.jpg')][:1]
        if not flyers:
            print("❌ No flyer images found")
            return
            
        test_image = os.path.join(flyer_dir, flyers[0])
        print(f"Using test image: {test_image}")
        
        # Method 1: Try uploading to various endpoints with different field names
        upload_endpoints = ["/api/upload", "/upload", "/api/media", "/media"]
        field_names = ["image", "media", "file", "upload"]
        
        for endpoint in upload_endpoints:
            for field_name in field_names:
                try:
                    with open(test_image, 'rb') as img_file:
                        files = {field_name: (os.path.basename(test_image), img_file, 'image/jpeg')}
                        resp = self.session.post(f"{self.gancio_base_url}{endpoint}", files=files)
                        
                        if resp.status_code not in [404, 405]:
                            print(f"POST {endpoint} with {field_name}: {resp.status_code}")
                            if resp.status_code < 400:
                                print(f"     Response: {resp.text[:100]}")
                                
                except Exception as e:
                    pass

    def check_event_creation_with_image(self):
        """Test creating an event with image in single request"""
        print("\n🔄 Testing Event Creation with Image...")
        
        # Get a test image
        flyer_dir = "flyers"
        if os.path.exists(flyer_dir):
            flyers = [f for f in os.listdir(flyer_dir) if f.endswith('.jpg')][:1]
            if flyers:
                test_image = os.path.join(flyer_dir, flyers[0])
                
                # Try multipart form data with event data and image
                from datetime import datetime, timedelta
                start_time = datetime.now() + timedelta(days=1)
                
                event_data = {
                    'title': 'API TEST - Image Upload',
                    'description': 'Testing API image upload',
                    'start_datetime': str(int(start_time.timestamp())),
                    'placeId': '1'
                }
                
                try:
                    with open(test_image, 'rb') as img_file:
                        files = {'image': (os.path.basename(test_image), img_file, 'image/jpeg')}
                        
                        # Test different endpoints
                        for endpoint in ["/add", "/api/event", "/api/events"]:
                            resp = self.session.post(
                                f"{self.gancio_base_url}{endpoint}", 
                                data=event_data,
                                files=files
                            )
                            print(f"Multipart {endpoint}: {resp.status_code}")
                            if resp.status_code < 400:
                                print(f"     Success response length: {len(resp.text)}")
                                
                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    investigator = GancioAPIInvestigator()
    
    print("🔐 Authenticating...")
    if investigator.authenticate():
        print("✅ Authenticated")
        investigator.test_api_endpoints()
        investigator.investigate_existing_events()  
        investigator.test_image_upload_methods()
        investigator.check_event_creation_with_image()
    else:
        print("❌ Authentication failed")
