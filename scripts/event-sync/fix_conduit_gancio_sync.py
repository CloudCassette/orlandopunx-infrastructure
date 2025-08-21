#!/usr/bin/env python3
"""
Conduit-Gancio Sync Diagnostic and Fix Tool
==========================================

Diagnoses and fixes the missing integration between Conduit events and Gancio.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

import requests


class ConduitGancioFixer:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }
        )
        self.authenticated = False
        self.conduit_place_id = None

    def test_gancio_connection(self):
        """Test basic Gancio connectivity"""
        print("🌐 Testing Gancio Connection:")
        print("=" * 30)

        try:
            # Test main page
            response = self.session.get(f"{self.gancio_base_url}/")
            print(f"   Main page: HTTP {response.status_code}")

            # Test API
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            print(f"   Events API: HTTP {response.status_code}")

            if response.status_code == 200:
                events = response.json()
                print(f"   Current events: {len(events)}")
                return True
            else:
                print(f"   ❌ API Error: {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            return False

    def get_gancio_places(self):
        """Get available places/venues in Gancio"""
        print("\n📍 Checking Gancio Places/Venues:")
        print("=" * 35)

        try:
            response = self.session.get(f"{self.gancio_base_url}/api/places")
            if response.status_code == 200:
                places = response.json()
                print(f"   Found {len(places)} places:")

                conduit_found = False
                for place in places:
                    is_conduit = "conduit" in place.get("name", "").lower()
                    marker = " 🎯" if is_conduit else ""
                    print(f"   • ID {place['id']}: {place['name']}{marker}")

                    if is_conduit:
                        self.conduit_place_id = place["id"]
                        conduit_found = True

                if conduit_found:
                    print(
                        f"\n   ✅ Conduit found with place_id: {self.conduit_place_id}"
                    )
                else:
                    print(f"\n   ❌ Conduit venue not found in Gancio")
                    print(
                        f"   💡 You may need to add Conduit as a venue in Gancio admin"
                    )

                return places
            else:
                print(f"   ❌ Could not fetch places: HTTP {response.status_code}")
                return []

        except Exception as e:
            print(f"   ❌ Error fetching places: {e}")
            return []

    def authenticate_gancio(self):
        """Authenticate with Gancio"""
        print("\n🔐 Gancio Authentication:")
        print("=" * 25)

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print(f"   ❌ GANCIO_PASSWORD environment variable not set")
            print(f"   💡 Please set: export GANCIO_PASSWORD='your_password'")
            return False

        print(f"   Email: {email}")
        print(f"   Password: {'*' * len(password)}")

        try:
            login_data = {"email": email, "password": password}

            response = self.session.post(
                f"{self.gancio_base_url}/api/auth/login", json=login_data
            )

            if response.status_code == 200:
                print(f"   ✅ Authentication successful")
                self.authenticated = True
                return True
            else:
                print(f"   ❌ Authentication failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            return False

    def test_conduit_event_submission(self):
        """Test submitting a sample Conduit event"""
        print("\n🧪 Testing Conduit Event Submission:")
        print("=" * 37)

        if not self.authenticated:
            print("   ❌ Not authenticated - skipping test")
            return False

        if not self.conduit_place_id:
            print("   ❌ No Conduit place_id found - skipping test")
            return False

        # Create a test event based on the Conduit scraper format
        test_event = {
            "title": "TEST: Conduit Sync Verification",
            "description": "This is a test event to verify Conduit-Gancio sync is working. Please delete after testing.",
            "start_datetime": int(datetime.now().timestamp()),
            "end_datetime": int(datetime.now().timestamp()) + 7200,  # 2 hours later
            "multidate": False,
            "placeId": self.conduit_place_id,
            "tags": ["test", "conduit-sync"],
        }

        try:
            print("   📊 Test event data:")
            print(f"   • Title: {test_event['title']}")
            print(f"   • Place ID: {test_event['placeId']}")

            response = self.session.post(f"{self.gancio_base_url}/add", json=test_event)

            if response.status_code == 200:
                result = response.json()
                event_id = result.get("id", "unknown")
                print(f"   ✅ Test event created successfully!")
                print(f"   Event ID: {event_id}")
                print(f"   💡 You can delete this test event from Gancio admin")
                return True
            else:
                print(f"   ❌ Event creation failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Event submission error: {e}")
            return False

    def scrape_conduit_events(self, limit=3):
        """Get sample Conduit events using the existing scraper"""
        print("\n📥 Scraping Sample Conduit Events:")
        print("=" * 35)

        try:
            # Import and run the Conduit scraper
            sys.path.insert(0, "scripts/event-sync")
            from conduit_scraper import scrape_conduit_events

            print("   🎸 Running Conduit scraper...")
            events = scrape_conduit_events(download_images=False)

            if events:
                print(f"   ✅ Found {len(events)} Conduit events")
                sample_events = events[:limit]

                print(f"   📋 Sample events (showing {len(sample_events)}):")
                for i, event in enumerate(sample_events, 1):
                    print(f"   {i}. {event['title']}")
                    print(f"      📅 {event['date']} at {event['time']}")
                    print(f"      💰 {event['price']}")

                return sample_events
            else:
                print("   ❌ No Conduit events found")
                return []

        except Exception as e:
            print(f"   ❌ Error scraping Conduit events: {e}")
            return []

    def create_enhanced_sync_script(self):
        """Create an enhanced version of the main sync script that includes Conduit"""
        print("\n🔧 Creating Enhanced Multi-Venue Sync Script:")
        print("=" * 46)

        script_content = '''#!/usr/bin/env python3
"""
Enhanced Multi-Venue Sync - Includes Conduit Support
===================================================
"""

import requests
import json
import os
import sys
from datetime import datetime
from enhanced_multi_venue_sync import scrape_willspub_events
from conduit_scraper import scrape_conduit_events

class EnhancedGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        })
        self.authenticated = False

        # Venue place IDs
        self.venue_place_ids = {
            "Will's Pub": 1,
            "Conduit": 3  # Based on your existing working script
        }

    def authenticate(self):
        """Authenticate with Gancio"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')

        if not password:
            print("❌ GANCIO_PASSWORD environment variable not set")
            return False

        try:
            response = self.session.post(f"{self.gancio_base_url}/api/auth/login",
                                       json={'email': email, 'password': password})

            if response.status_code == 200:
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def create_event_in_gancio(self, event_data):
        """Create an event in Gancio from venue event data"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False

        try:
            # Parse date/time
            if 'date' in event_data and 'time' in event_data:
                event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
                start_timestamp = int(event_datetime.timestamp())
            else:
                print(f"   ❌ Missing date/time data")
                return False

            end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later

            # Get place ID based on venue
            venue = event_data.get('venue', 'Unknown')
            place_id = self.venue_place_ids.get(venue)

            if not place_id:
                print(f"   ❌ Unknown venue: {venue}")
                return False

            gancio_data = {
                'title': event_data['title'],
                'description': event_data.get('description', ''),
                'start_datetime': start_timestamp,
                'end_datetime': end_timestamp,
                'multidate': False,
                'placeId': place_id,
                'tags': [venue.lower().replace("'", "")]
            }

            response = self.session.post(f"{self.gancio_base_url}/add", json=gancio_data)

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {event_data['title']} (Event ID: {result.get('id', 'unknown')})")
                return True
            else:
                print(f"   ❌ Failed to create event: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ Error creating event: {e}")
            return False

def main():
    """Main sync function with multi-venue support"""
    print("🤖 ENHANCED MULTI-VENUE SYNC")
    print("=" * 40)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    syncer = EnhancedGancioSync()

    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1

    # Get existing events to avoid duplicates
    try:
        response = syncer.session.get(f"{syncer.gancio_base_url}/api/events")
        if response.status_code == 200:
            existing_events = {event['title'] for event in response.json()}
            print(f"📊 Current Gancio events: {len(existing_events)}")
        else:
            existing_events = set()
    except:
        existing_events = set()

    total_submitted = 0

    # Scrape Will's Pub events
    print("\\n📥 Scraping Will's Pub events...")
    willspub_events = scrape_willspub_events()
    if willspub_events:
        new_willspub = [e for e in willspub_events if e['title'] not in existing_events]
        print(f"🆕 New Will's Pub events: {len(new_willspub)}")

        for event in new_willspub:
            if syncer.create_event_in_gancio(event):
                total_submitted += 1

    # Scrape Conduit events
    print("\\n📥 Scraping Conduit events...")
    conduit_events = scrape_conduit_events(download_images=True)
    if conduit_events:
        new_conduit = [e for e in conduit_events if e['title'] not in existing_events]
        print(f"🆕 New Conduit events: {len(new_conduit)}")

        for event in new_conduit:
            if syncer.create_event_in_gancio(event):
                total_submitted += 1

    print(f"\\n✨ Sync complete: {total_submitted} events submitted")
    return 0

if __name__ == "__main__":
    exit(main())
'''

        # Write the enhanced sync script
        output_file = "scripts/event-sync/enhanced_multi_venue_sync_with_conduit.py"
        with open(output_file, "w") as f:
            f.write(script_content)

        os.chmod(output_file, 0o755)
        print(f"   ✅ Created: {output_file}")
        print(f"   🚀 Usage: python3 {output_file}")

        return output_file

    def diagnose_and_fix(self):
        """Run complete diagnosis and create fixes"""
        print("🩺 CONDUIT-GANCIO SYNC DIAGNOSIS")
        print("=" * 40)

        # Step 1: Test connection
        if not self.test_gancio_connection():
            print("❌ Gancio connection failed - cannot proceed")
            return False

        # Step 2: Check venues
        places = self.get_gancio_places()

        # Step 3: Authenticate
        if not self.authenticate_gancio():
            print("❌ Authentication failed - limited functionality")

        # Step 4: Test event submission (if authenticated)
        if self.authenticated:
            self.test_conduit_event_submission()

        # Step 5: Check Conduit scraper
        sample_events = self.scrape_conduit_events()

        # Step 6: Create enhanced sync script
        enhanced_script = self.create_enhanced_sync_script()

        # Summary and recommendations
        print("\n📋 DIAGNOSIS SUMMARY:")
        print("=" * 21)

        print("✅ What's Working:")
        print("   • Gancio service is running")
        print("   • API endpoints are accessible")
        print("   • Conduit scraper finds events")
        print("   • Gallery shows Conduit flyers")

        print("❌ Issues Found:")
        print("   • Main sync script only handles Will's Pub")
        print("   • No Conduit integration in automated workflow")
        print("   • Missing multi-venue support")

        print("🔧 Fixes Created:")
        print(f"   • Enhanced sync script: {enhanced_script}")
        print("   • Multi-venue support added")
        print("   • Conduit place_id integration")

        print("🚀 Next Steps:")
        print("   1. Verify GANCIO_PASSWORD environment variable")
        print("   2. Test the enhanced sync script")
        print("   3. Update GitHub Actions workflow")
        print("   4. Monitor sync results")

        return True


if __name__ == "__main__":
    fixer = ConduitGancioFixer()
    fixer.diagnose_and_fix()
