#!/usr/bin/env python3
"""
Authentication Debug and Manual Sync Tool
==========================================
Debug authentication issues and provide manual sync capabilities
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests


class AuthDebugger:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

    def debug_gancio_auth_methods(self):
        """Deep debug of Gancio authentication methods"""
        print("🔍 DEEP AUTHENTICATION DEBUG")
        print("=" * 35)

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD not set")
            return False

        print(f"📧 Email: {email}")

        # Step 1: Explore available endpoints
        print("\n🔍 Discovering authentication endpoints...")

        endpoints_to_check = [
            "/login",
            "/auth",
            "/auth/login",
            "/admin",
            "/admin/login",
            "/api/auth",
            "/api/auth/login",
        ]

        available_endpoints = []
        for endpoint in endpoints_to_check:
            try:
                response = self.session.get(f"{self.gancio_base_url}{endpoint}")
                print(
                    f"   {endpoint}: HTTP {response.status_code} ({len(response.text)} chars)"
                )

                if response.status_code in [200, 302, 401, 403]:
                    available_endpoints.append(endpoint)

                    # Check for form fields or auth hints
                    if (
                        "password" in response.text.lower()
                        or "login" in response.text.lower()
                    ):
                        print(f"      ✅ Contains auth-related content")

            except Exception as e:
                print(f"   {endpoint}: Error - {e}")

        # Step 2: Try different authentication approaches
        print(f"\n🔐 Testing authentication approaches...")

        # Method 1: Session-based login like browser
        print("🧪 Method 1: Session-based browser-like login...")
        try:
            # Get login page first
            login_response = self.session.get(f"{self.gancio_base_url}/login")
            print(f"   Login page: {login_response.status_code}")

            # Look for CSRF tokens or hidden fields
            csrf_token = self.extract_csrf_token(login_response.text)
            if csrf_token:
                print(f"   Found CSRF token: {csrf_token[:20]}...")

            # Try form submission
            login_data = {"email": email, "password": password}
            if csrf_token:
                login_data["_token"] = csrf_token

            # Post to /auth/login with proper headers
            auth_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{self.gancio_base_url}/login",
            }

            auth_response = self.session.post(
                f"{self.gancio_base_url}/auth/login",
                data=login_data,
                headers=auth_headers,
                allow_redirects=False,
            )

            print(f"   Auth POST: {auth_response.status_code}")
            if "Location" in auth_response.headers:
                print(f"   Redirect to: {auth_response.headers['Location']}")

            # Follow redirect if any
            if auth_response.status_code in [302, 301]:
                final_response = self.session.get(
                    auth_response.headers.get("Location", "/")
                )
                print(f"   Final page: {final_response.status_code}")

                if "admin" in final_response.url:
                    print("   ✅ Successfully redirected to admin!")
                    return True

        except Exception as e:
            print(f"   ❌ Session method error: {e}")

        # Method 2: Direct API authentication
        print("\n🧪 Method 2: Direct API authentication...")

        api_endpoints = [
            ("/api/auth/login", {"email": email, "password": password}),
            ("/api/login", {"email": email, "password": password}),
            ("/auth", {"email": email, "password": password}),
        ]

        for endpoint, data in api_endpoints:
            try:
                # Try JSON
                json_response = self.session.post(
                    f"{self.gancio_base_url}{endpoint}", json=data
                )
                print(f"   {endpoint} (JSON): {json_response.status_code}")

                if json_response.status_code == 200:
                    print("   ✅ JSON auth successful!")
                    return True

                # Try form data
                form_response = self.session.post(
                    f"{self.gancio_base_url}{endpoint}", data=data
                )
                print(f"   {endpoint} (Form): {form_response.status_code}")

                if form_response.status_code == 200:
                    print("   ✅ Form auth successful!")
                    return True

            except Exception as e:
                print(f"   ❌ {endpoint} error: {e}")

        # Method 3: Check if already authenticated somehow
        print("\n🧪 Method 3: Check existing authentication...")
        try:
            admin_response = self.session.get(f"{self.gancio_base_url}/admin")
            print(f"   Admin access: {admin_response.status_code}")

            if (
                admin_response.status_code == 200
                and "admin" in admin_response.text.lower()
            ):
                print("   ✅ Already authenticated!")
                return True

        except Exception as e:
            print(f"   ❌ Admin check error: {e}")

        print("\n❌ All authentication methods failed")
        return False

    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML"""
        patterns = [
            r'<input[^>]*name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']',
            r'_token["\']?\s*:\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def manual_event_creation_guide(self):
        """Provide manual event creation guidance"""
        print("\n📋 MANUAL EVENT CREATION GUIDE")
        print("=" * 35)

        print(
            "Since automatic authentication failed, here's how to manually add events:"
        )

        print(f"\n1. 🌐 Open Gancio Admin:")
        print(f"   URL: {self.gancio_base_url}/admin")
        print(f"   Login with: godlessamericarecords@gmail.com")

        print(f"\n2. 📝 Add Missing Conduit Events:")
        print(f"   • Venue: Conduit (place_id: 3)")
        print(f"   • Missing events: 19")

        # Get sample Conduit events to show
        try:
            sys.path.insert(0, "scripts/event-sync")
            from conduit_scraper import scrape_conduit_events

            conduit_events = scrape_conduit_events(download_images=False)
            if conduit_events:
                print(f"\n   📋 Sample Conduit events to add manually:")
                for i, event in enumerate(conduit_events[:5], 1):
                    print(f"   {i}. {event['title']}")
                    print(f"      📅 {event['date']} at {event['time']}")
                    print(f"      💰 {event['price']}")
                    print("")

                if len(conduit_events) > 5:
                    print(f"   ... and {len(conduit_events) - 5} more events")

        except Exception as e:
            print(f"   ❌ Could not load Conduit events: {e}")

        print(f"\n3. ✅ Verify Will's Pub Events:")
        print(f"   • Current in Gancio: 13")
        print(f"   • Should have: ~20")
        print(f"   • Check for missing recent events")

    def create_bypass_sync_script(self):
        """Create a script that bypasses authentication by working with existing sessions"""
        print("\n🔧 CREATING BYPASS SYNC SCRIPT")
        print("=" * 35)

        script_content = '''#!/usr/bin/env python3
"""
Bypass Authentication Sync - Manual Helper
==========================================
Use this after manually logging into Gancio admin
"""

import json
import requests
from datetime import datetime

def create_manual_sync_data():
    """Create JSON data for manual import"""
    import sys
    sys.path.insert(0, 'scripts/event-sync')

    try:
        from conduit_scraper import scrape_conduit_events
        from enhanced_multi_venue_sync import scrape_willspub_events

        print("🎤 Getting Conduit events...")
        conduit_events = scrape_conduit_events(download_images=False)

        print("🎸 Getting Will's Pub events...")
        willspub_events = scrape_willspub_events()

        # Format for manual import
        manual_data = {
            "conduit": [],
            "willspub": []
        }

        for event in conduit_events or []:
            manual_data["conduit"].append({
                "title": event["title"],
                "date": event["date"],
                "time": event["time"],
                "description": event.get("description", "Live music at Conduit"),
                "venue": "Conduit",
                "place_id": 3
            })

        for event in willspub_events or []:
            manual_data["willspub"].append({
                "title": event["title"],
                "datetime": event["datetime"].isoformat() if hasattr(event.get("datetime"), "isoformat") else str(event.get("datetime")),
                "description": event.get("description", "Live music at Will's Pub"),
                "venue": "Will's Pub",
                "place_id": 1
            })

        # Save to file
        with open("manual_sync_data.json", "w") as f:
            json.dump(manual_data, f, indent=2, default=str)

        print(f"✅ Created manual_sync_data.json with:")
        print(f"   • Conduit events: {len(manual_data['conduit'])}")
        print(f"   • Will's Pub events: {len(manual_data['willspub'])}")
        print()
        print("💡 Use this data to manually add events in Gancio admin")

    except Exception as e:
        print(f"❌ Error creating manual data: {e}")

if __name__ == "__main__":
    create_manual_sync_data()
'''

        with open("scripts/event-sync/manual_sync_helper.py", "w") as f:
            f.write(script_content)

        os.chmod("scripts/event-sync/manual_sync_helper.py", 0o755)
        print("✅ Created: scripts/event-sync/manual_sync_helper.py")
        print("🚀 Run with: python3 scripts/event-sync/manual_sync_helper.py")

    def run_complete_auth_debug(self):
        """Run complete authentication debugging"""
        print("🔐 AUTHENTICATION DEBUG & MANUAL SYNC TOOLS")
        print("=" * 50)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Debug authentication
        auth_success = self.debug_gancio_auth_methods()

        if not auth_success:
            # Provide manual alternatives
            self.manual_event_creation_guide()
            self.create_bypass_sync_script()

            print("\n💡 RECOMMENDED NEXT STEPS:")
            print("=" * 30)
            print("1. 🌐 Login to Gancio manually:")
            print(f"   {self.gancio_base_url}/admin")
            print()
            print("2. 📊 Generate manual sync data:")
            print("   python3 scripts/event-sync/manual_sync_helper.py")
            print()
            print("3. 📝 Use the generated JSON to manually add missing events")
            print()
            print("4. 🔧 Alternative: Check Gancio documentation for API auth")

        else:
            print("✅ Authentication successful - automated sync should work")


if __name__ == "__main__":
    debugger = AuthDebugger()
    debugger.run_complete_auth_debug()
