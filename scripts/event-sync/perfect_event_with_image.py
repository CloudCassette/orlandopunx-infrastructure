#!/usr/bin/env python3
"""
Perfect Event Creation with Image - Based on Investigation Results
"""

import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()


class PerfectGancioImageUpload:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

    def authenticate(self):
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        try:
            login_data = {"email": email, "password": password}
            resp = self.session.post(f"{self.gancio_base_url}/login", data=login_data)
            return resp.status_code == 200
        except:
            return False

    def analyze_working_event_creation(self):
        """Create an event using the exact method that works, then add image"""
        print("🔍 Analyzing working event creation method...")

        # Use the EXACT method from the working script
        start_time = datetime.now() + timedelta(days=3)
        start_timestamp = int(start_time.timestamp())
        end_timestamp = start_timestamp + (3 * 3600)

        # EXACT format from working script
        gancio_event = {
            "title": "PERFECT TEST - Image Upload Analysis",
            "start_datetime": start_timestamp,
            "end_datetime": end_timestamp,
            "description": "Testing perfect image upload",
            "tags": ["willspub", "live-music", "orlando"],
            "placeId": 1,
            "multidate": False,
        }

        print(f"📤 Creating event with JSON method...")
        print(f"   Data: {gancio_event}")

        # Set headers like the working script
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        }

        try:
            resp = self.session.post(
                f"{self.gancio_base_url}/add",
                json=gancio_event,
                headers=headers,
                timeout=30,
            )

            print(f"   Status: {resp.status_code}")
            print(f"   Response length: {len(resp.text)}")

            if resp.status_code == 200:
                print("✅ Event created successfully!")
                return True
            else:
                print(f"   Response: {resp.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_multipart_with_better_data(self):
        """Test multipart form with better structured data"""
        print("\n🖼️  Testing multipart form with proper data...")

        # Get a good test image
        flyer_dir = "flyers"
        if not os.path.exists(flyer_dir):
            print("❌ No flyers directory")
            return False

        # Find a real event flyer (not Buy_Tickets)
        flyers = [
            f
            for f in os.listdir(flyer_dir)
            if f.endswith(".jpg") and not f.startswith("Buy_Tickets")
        ]
        if not flyers:
            print("❌ No good flyers found")
            return False

        test_image = os.path.join(flyer_dir, flyers[0])
        print(f"   Using image: {os.path.basename(test_image)}")

        # Create form data that matches the web form exactly
        start_time = datetime.now() + timedelta(days=2)
        start_timestamp = int(start_time.timestamp())
        end_timestamp = start_timestamp + (3 * 3600)

        # Form data matching web interface
        form_data = {
            "title": "PERFECT TEST - With Real Image",
            "description": "Testing multipart form with real image",
            "start_datetime": str(start_timestamp),
            "end_datetime": str(end_timestamp),
            "placeId": "1",  # String format like web form
            "tags": '["test", "image"]',  # JSON string format
            "multidate": "false",
        }

        print(f"   Form data: {form_data}")

        try:
            with open(test_image, "rb") as img_file:
                # Remove content-type header for multipart
                headers = {
                    k: v
                    for k, v in self.session.headers.items()
                    if k.lower() != "content-type"
                }

                files = {
                    "image": (os.path.basename(test_image), img_file, "image/jpeg")
                }

                resp = self.session.post(
                    f"{self.gancio_base_url}/add",
                    data=form_data,
                    files=files,
                    headers=headers,
                    timeout=30,
                )

                print(f"   Status: {resp.status_code}")
                print(f"   Response length: {len(resp.text)}")

                if resp.status_code == 200:
                    # Check if it's the form again or success
                    if "Nuovo evento" in resp.text:
                        print("   ⚠️  Form returned - checking for errors...")
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(resp.text, "html.parser")
                        errors = soup.find_all(
                            ["div", "span"], class_=["error", "v-messages__message"]
                        )
                        for error in errors:
                            if error.text.strip() and "opzionale" not in error.text:
                                print(f"      Error: {error.text.strip()}")
                        return False
                    else:
                        print("✅ Success - no form returned")
                        return True
                else:
                    print(f"   ❌ HTTP Error: {resp.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def check_created_events(self):
        """Check if our test events were created"""
        print("\n📊 Checking created events...")

        try:
            resp = self.session.get(f"{self.gancio_base_url}/api/events")
            if resp.status_code == 200:
                events = resp.json()

                test_events = [
                    e for e in events if "PERFECT TEST" in e.get("title", "")
                ]
                print(f"Found {len(test_events)} test events")

                for event in test_events:
                    print(f"\n✅ {event['title']}")
                    print(f"   ID: {event['id']}")
                    print(
                        f"   Has media: {'media' in event and len(event['media']) > 0}"
                    )
                    if "media" in event and event["media"]:
                        for media in event["media"]:
                            print(
                                f"   📷 Image: {media['url']} ({media['width']}x{media['height']})"
                            )

                return len(test_events) > 0
            else:
                print(f"❌ API error: {resp.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False


if __name__ == "__main__":
    uploader = PerfectGancioImageUpload()

    if uploader.authenticate():
        print("✅ Authenticated")

        # Test both methods
        uploader.analyze_working_event_creation()
        uploader.test_multipart_with_better_data()
        uploader.check_created_events()
    else:
        print("❌ Authentication failed")
