#!/usr/bin/env python3
"""
Reverse Engineer How Images Work in Gancio
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


class GancioImageReverseEngineering:
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

    def analyze_existing_images(self):
        """Analyze events that already have images"""
        print("🔍 Analyzing existing events with images...")

        try:
            resp = self.session.get(f"{self.gancio_base_url}/api/events")
            if resp.status_code == 200:
                events = resp.json()

                events_with_images = [e for e in events if "media" in e and e["media"]]
                print(f"Found {len(events_with_images)} events with images")

                for i, event in enumerate(events_with_images[:3]):
                    print(f"\n--- Event {i+1}: {event['title'][:50]} ---")
                    print(f"ID: {event['id']}")
                    print(f"Media: {event['media']}")

                    # Try to access the image directly
                    for media in event["media"]:
                        image_url = media["url"]
                        print(f"Testing image URL: {image_url}")

                        # Try different ways to access the image
                        test_urls = [
                            f"{self.gancio_base_url}/{image_url}",
                            f"{self.gancio_base_url}/media/{image_url}",
                            f"{self.gancio_base_url}/uploads/{image_url}",
                            f"{self.gancio_base_url}/images/{image_url}",
                            f"{self.gancio_base_url}/static/{image_url}",
                        ]

                        for url in test_urls:
                            try:
                                resp = self.session.get(url)
                                if resp.status_code == 200:
                                    print(f"   ✅ Image accessible at: {url}")
                                    print(
                                        f"   Content-Type: {resp.headers.get('content-type', 'unknown')}"
                                    )
                                    print(f"   Size: {len(resp.content)} bytes")
                                    break
                            except:
                                pass
                        else:
                            print(f"   ❌ Image not accessible via standard URLs")

                return events_with_images
            else:
                print(f"❌ API error: {resp.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def check_admin_endpoints(self):
        """Check if there are admin-specific endpoints for image upload"""
        print("\n🔧 Checking admin endpoints...")

        admin_endpoints = [
            "/admin",
            "/admin/events",
            "/admin/media",
            "/admin/upload",
            "/admin/api/events",
            "/admin/api/media",
        ]

        for endpoint in admin_endpoints:
            try:
                resp = self.session.get(f"{self.gancio_base_url}{endpoint}")
                print(f"GET {endpoint}: {resp.status_code}")

                if resp.status_code == 200:
                    print(f"   Content length: {len(resp.text)}")
                    if "upload" in resp.text.lower() or "media" in resp.text.lower():
                        print("   ✅ Contains upload/media references")

            except Exception as e:
                print(f"{endpoint}: Error - {e}")

    def test_form_analysis(self):
        """Analyze the actual form structure for clues"""
        print("\n📝 Analyzing form structure...")

        try:
            # Get the add event form
            resp = self.session.get(f"{self.gancio_base_url}/add")
            if resp.status_code == 200:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(resp.text, "html.parser")

                # Look for file inputs
                file_inputs = soup.find_all("input", {"type": "file"})
                print(f"Found {len(file_inputs)} file inputs:")
                for inp in file_inputs:
                    print(
                        f"   - {inp.get('name', 'no name')} (accept: {inp.get('accept', 'any')})"
                    )
                    print(f"     ID: {inp.get('id', 'no id')}")

                # Look for form action
                forms = soup.find_all("form")
                for form in forms:
                    action = form.get("action", "no action")
                    method = form.get("method", "GET")
                    enctype = form.get("enctype", "application/x-www-form-urlencoded")
                    print(
                        f"Form: action='{action}' method='{method}' enctype='{enctype}'"
                    )

                # Look for Vue.js or JavaScript clues
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.get("src"):
                        print(f"Script: {script['src']}")
                    elif "upload" in script.text.lower():
                        print("Found upload-related JavaScript")

        except Exception as e:
            print(f"❌ Error: {e}")

    def test_csrf_and_headers(self):
        """Check if CSRF tokens or special headers are needed"""
        print("\n🔐 Checking CSRF and headers...")

        try:
            # Get the form page and look for CSRF tokens
            resp = self.session.get(f"{self.gancio_base_url}/add")
            if resp.status_code == 200:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(resp.text, "html.parser")

                # Look for CSRF tokens
                csrf_inputs = soup.find_all(
                    "input", {"name": ["_token", "csrf_token", "_csrf"]}
                )
                for inp in csrf_inputs:
                    print(
                        f"CSRF token: {inp.get('name')} = {inp.get('value', 'no value')[:20]}..."
                    )

                # Look for meta tags with tokens
                meta_tokens = soup.find_all("meta", {"name": ["csrf-token", "_token"]})
                for meta in meta_tokens:
                    print(
                        f"Meta token: {meta.get('name')} = {meta.get('content', 'no content')[:20]}..."
                    )

                # Check response headers
                print("Response headers:")
                for key, value in resp.headers.items():
                    if any(
                        keyword in key.lower() for keyword in ["csrf", "token", "xsrf"]
                    ):
                        print(f"   {key}: {value}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    analyzer = GancioImageReverseEngineering()

    if analyzer.authenticate():
        print("✅ Authenticated")
        analyzer.analyze_existing_images()
        analyzer.check_admin_endpoints()
        analyzer.test_form_analysis()
        analyzer.test_csrf_and_headers()
    else:
        print("❌ Authentication failed")
