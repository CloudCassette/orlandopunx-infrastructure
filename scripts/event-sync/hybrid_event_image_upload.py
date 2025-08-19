#!/usr/bin/env python3
"""
Hybrid Approach: Create Event + Update with Image
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

load_dotenv()

class HybridGancioUpload:
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

    def create_event_json(self):
        """Create event using working JSON method"""
        print("📝 Creating event with JSON (working method)...")
        
        start_time = datetime.now() + timedelta(days=1)
        start_timestamp = int(start_time.timestamp())
        end_timestamp = start_timestamp + (3 * 3600)
        
        gancio_event = {
            "title": "HYBRID TEST - Event Then Image",
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "description": "Testing hybrid approach: create event, then add image",
            "tags": ["willspub", "live-music", "orlando"],
            "placeId": 1,
            "multidate": False
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            resp = self.session.post(
                f"{self.gancio_base_url}/add",
                json=gancio_event,
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 200:
                print("✅ Event created successfully!")
                return True
            else:
                print(f"❌ Failed: {resp.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def find_created_event(self):
        """Find the event we just created"""
        print("🔍 Finding created event...")
        
        try:
            resp = self.session.get(f"{self.gancio_base_url}/api/events")
            if resp.status_code == 200:
                events = resp.json()
                
                for event in events:
                    if 'HYBRID TEST' in event.get('title', ''):
                        print(f"✅ Found event: {event['title']} (ID: {event['id']})")
                        return event
                
                print("❌ Event not found")
                return None
            else:
                print(f"❌ API error: {resp.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def try_update_event_with_image(self, event_id):
        """Try various methods to add image to existing event"""
        print(f"🖼️  Trying to add image to event {event_id}...")
        
        # Get test image
        flyer_dir = "flyers"
        if not os.path.exists(flyer_dir):
            print("❌ No flyers directory")
            return False
            
        flyers = [f for f in os.listdir(flyer_dir) if f.endswith('.jpg') and not f.startswith('Buy_Tickets')]
        if not flyers:
            print("❌ No good flyers found")
            return False
            
        test_image = os.path.join(flyer_dir, flyers[0])
        print(f"   Using: {os.path.basename(test_image)}")
        
        # Try different update methods
        update_endpoints = [
            f"/api/event/{event_id}",
            f"/api/events/{event_id}",
            f"/api/event/{event_id}/media",
            f"/api/event/{event_id}/image",
            f"/event/{event_id}/edit",
            f"/edit/{event_id}"
        ]
        
        for endpoint in update_endpoints:
            print(f"   Testing: {endpoint}")
            
            try:
                with open(test_image, 'rb') as img_file:
                    # Method 1: PATCH with multipart
                    files = {'image': (os.path.basename(test_image), img_file, 'image/jpeg')}
                    resp = self.session.patch(f"{self.gancio_base_url}{endpoint}", files=files)
                    print(f"      PATCH: {resp.status_code}")
                    
                    # Method 2: PUT with multipart
                    img_file.seek(0)
                    resp = self.session.put(f"{self.gancio_base_url}{endpoint}", files=files)
                    print(f"      PUT: {resp.status_code}")
                    
                    # Method 3: POST with multipart
                    img_file.seek(0)
                    resp = self.session.post(f"{self.gancio_base_url}{endpoint}", files=files)
                    print(f"      POST: {resp.status_code}")
                    
                    if resp.status_code < 400:
                        print(f"      ✅ Success response: {resp.text[:100]}")
                        return True
                        
            except Exception as e:
                print(f"      Error: {e}")
                
        return False

    def test_direct_media_upload(self):
        """Try uploading image to media endpoint first"""
        print("\n📤 Testing direct media upload...")
        
        # Get test image
        flyer_dir = "flyers"
        flyers = [f for f in os.listdir(flyer_dir) if f.endswith('.jpg') and not f.startswith('Buy_Tickets')]
        if not flyers:
            return None
            
        test_image = os.path.join(flyer_dir, flyers[0])
        
        # Try uploading to potential media endpoints
        media_endpoints = [
            "/media",
            "/upload", 
            "/api/media",
            "/api/upload",
            "/api/files"
        ]
        
        for endpoint in media_endpoints:
            try:
                with open(test_image, 'rb') as img_file:
                    files = {'file': (os.path.basename(test_image), img_file, 'image/jpeg')}
                    resp = self.session.post(f"{self.gancio_base_url}{endpoint}", files=files)
                    print(f"{endpoint}: {resp.status_code}")
                    
                    if resp.status_code < 400:
                        print(f"   Success: {resp.text[:200]}")
                        try:
                            return resp.json()
                        except:
                            return resp.text
                            
            except Exception as e:
                print(f"{endpoint}: Error - {e}")
                
        return None

    def check_final_result(self):
        """Check if image was added to event"""
        print("\n📊 Checking final result...")
        
        try:
            resp = self.session.get(f"{self.gancio_base_url}/api/events")
            if resp.status_code == 200:
                events = resp.json()
                
                for event in events:
                    if 'HYBRID TEST' in event.get('title', ''):
                        print(f"✅ Event: {event['title']}")
                        print(f"   Has media: {'media' in event and len(event['media']) > 0}")
                        if 'media' in event and event['media']:
                            for media in event['media']:
                                print(f"   📷 Image: {media['url']} ({media['width']}x{media['height']})")
                        return True
                        
                print("❌ Event not found")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    uploader = HybridGancioUpload()
    
    if uploader.authenticate():
        print("✅ Authenticated")
        
        # Step 1: Create event
        if uploader.create_event_json():
            time.sleep(2)  # Give it a moment
            
            # Step 2: Find the event
            event = uploader.find_created_event()
            if event:
                # Step 3: Try to add image
                uploader.try_update_event_with_image(event['id'])
                
        # Step 4: Test direct media upload
        uploader.test_direct_media_upload()
        
        # Step 5: Check results
        uploader.check_final_result()
        
    else:
        print("❌ Authentication failed")
