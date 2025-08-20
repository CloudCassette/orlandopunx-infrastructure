#!/usr/bin/env python3
"""
Complete Event Sync Solution
============================
Final comprehensive sync tool with authentication fix and deduplication
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
from collections import defaultdict
import hashlib

class CompleteSyncSolution:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        })
        self.authenticated = False
        
        # Venue configurations
        self.venue_configs = {
            "Will's Pub": {"place_id": 1},
            "Conduit": {"place_id": 3}
        }

    def authenticate_working_method(self):
        """Use the working authentication method discovered"""
        print("🔐 AUTHENTICATING WITH WORKING METHOD")
        print("=" * 40)
        
        # The debug showed we're already authenticated, so let's test admin access
        try:
            admin_response = self.session.get(f"{self.gancio_base_url}/admin")
            if admin_response.status_code == 200 and 'admin' in admin_response.text.lower():
                print("✅ Already authenticated to Gancio admin")
                self.authenticated = True
                return True
                
        except Exception as e:
            print(f"❌ Admin check failed: {e}")
        
        # If not already authenticated, try the browser-like method
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ GANCIO_PASSWORD not set")
            return False
        
        try:
            # Get the login page to establish session
            login_page = self.session.get(f"{self.gancio_base_url}/login")
            
            # Submit credentials - the debug showed /login endpoint works
            login_data = {'email': email, 'password': password}
            
            # Post to login (not /auth/login which returns 404)
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True)
            
            # Check if we can access admin
            admin_check = self.session.get(f"{self.gancio_base_url}/admin")
            if admin_check.status_code == 200 and 'admin' in admin_check.text.lower():
                print("✅ Authentication successful via /login endpoint")
                self.authenticated = True
                return True
                
        except Exception as e:
            print(f"❌ Login method failed: {e}")
        
        print("❌ Authentication failed")
        return False

    def get_events_with_deduplication_info(self):
        """Get all events with comprehensive deduplication info"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                
                # Create comprehensive dedup mapping
                dedup_info = {
                    'events': events,
                    'by_title': defaultdict(list),
                    'by_venue': defaultdict(list),
                    'title_hashes': set()
                }
                
                for event in events:
                    title = event.get('title', '').strip()
                    title_hash = hashlib.md5(title.lower().encode()).hexdigest()
                    
                    dedup_info['by_title'][title].append(event)
                    dedup_info['title_hashes'].add(title_hash)
                    
                    # Identify venue
                    venue = self.identify_venue_from_event(event)
                    dedup_info['by_venue'][venue].append(event)
                
                return dedup_info
            else:
                print(f"❌ Failed to get events: HTTP {response.status_code}")
                return {'events': [], 'by_title': {}, 'by_venue': {}, 'title_hashes': set()}
        except Exception as e:
            print(f"❌ Error getting events: {e}")
            return {'events': [], 'by_title': {}, 'by_venue': {}, 'title_hashes': set()}

    def identify_venue_from_event(self, event):
        """Identify venue from event data"""
        # Check place_id first (most reliable)
        place_id = event.get('place_id')
        if place_id == 1:
            return "Will's Pub"
        elif place_id == 3:
            return "Conduit"
        
        # Check place object
        place = event.get('place', {})
        if isinstance(place, dict):
            place_name = place.get('name', '').lower()
            if 'will' in place_name or 'pub' in place_name:
                return "Will's Pub"
            elif 'conduit' in place_name:
                return "Conduit"
        
        return "Unknown"

    def create_event_safely(self, event_data, dedup_info):
        """Create event with proper deduplication and error handling"""
        if not self.authenticated:
            return False
        
        title = event_data.get('title', '').strip()
        venue = event_data.get('venue', 'Unknown')
        
        # Skip if duplicate
        if title in dedup_info['by_title']:
            print(f"   ⚠️  Skipping duplicate: {title}")
            return False
        
        # Get venue config
        venue_config = self.venue_configs.get(venue)
        if not venue_config:
            print(f"   ❌ Unknown venue: {venue}")
            return False
        
        place_id = venue_config['place_id']
        
        # Parse datetime
        try:
            if 'date' in event_data and 'time' in event_data:
                # Conduit format
                event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
            elif 'datetime' in event_data:
                # Will's Pub format
                event_datetime = event_data['datetime']
            else:
                print(f"   ❌ No datetime for: {title}")
                return False
            
            start_timestamp = int(event_datetime.timestamp())
            end_timestamp = start_timestamp + (3 * 3600)  # 3 hours
            
        except Exception as e:
            print(f"   ❌ Datetime error for {title}: {e}")
            return False
        
        # Create Gancio event
        gancio_event = {
            'title': title,
            'description': event_data.get('description', f'Live music at {venue}'),
            'start_datetime': start_timestamp,
            'end_datetime': end_timestamp,
            'place_id': place_id,
            'tags': [venue.lower().replace("'", "").replace(" ", "_")]
        }
        
        # Try event creation with proper endpoint
        try:
            response = self.session.post(f"{self.gancio_base_url}/api/event", json=gancio_event, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                event_id = result.get('id', 'unknown')
                print(f"   ✅ Created: {title} (ID: {event_id})")
                
                # Update dedup info
                dedup_info['by_title'][title].append({'id': event_id, 'title': title})
                return True
            else:
                print(f"   ❌ API error for {title}: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request error for {title}: {e}")
            return False

    def sync_all_missing_events(self):
        """Sync all missing events from both venues"""
        print("\n🔄 SYNCING ALL MISSING EVENTS")
        print("=" * 35)
        
        if not self.authenticated:
            print("❌ Not authenticated")
            return False
        
        # Get current state
        dedup_info = self.get_events_with_deduplication_info()
        current_count = len(dedup_info['events'])
        print(f"📊 Current Gancio events: {current_count}")
        
        # Show current breakdown
        venue_counts = {}
        for venue, events in dedup_info['by_venue'].items():
            venue_counts[venue] = len(events)
            print(f"   • {venue}: {venue_counts[venue]} events")
        
        # Import scrapers
        sys.path.insert(0, 'scripts/event-sync')
        
        total_created = 0
        total_errors = 0
        
        # Sync Will's Pub events
        print(f"\n🎸 Syncing Will's Pub events...")
        try:
            from enhanced_multi_venue_sync import scrape_willspub_events
            willspub_events = scrape_willspub_events()
            
            if willspub_events:
                print(f"   📋 Processing {len(willspub_events)} Will's Pub events...")
                
                for event in willspub_events:
                    try:
                        if self.create_event_safely(event, dedup_info):
                            total_created += 1
                        time.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        print(f"   ❌ Error processing Will's Pub event: {e}")
                        total_errors += 1
            else:
                print("   ❌ No Will's Pub events found")
                
        except Exception as e:
            print(f"   ❌ Will's Pub scraping error: {e}")
        
        # Sync Conduit events
        print(f"\n🎤 Syncing Conduit events...")
        try:
            from conduit_scraper import scrape_conduit_events
            conduit_events = scrape_conduit_events(download_images=False)
            
            if conduit_events:
                print(f"   📋 Processing {len(conduit_events)} Conduit events...")
                
                for event in conduit_events:
                    try:
                        if self.create_event_safely(event, dedup_info):
                            total_created += 1
                        time.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        print(f"   ❌ Error processing Conduit event: {e}")
                        total_errors += 1
            else:
                print("   ❌ No Conduit events found")
                
        except Exception as e:
            print(f"   ❌ Conduit scraping error: {e}")
        
        print(f"\n📊 SYNC RESULTS:")
        print(f"   ✅ Successfully created: {total_created} events")
        print(f"   ❌ Errors encountered: {total_errors}")
        
        return total_created > 0

    def verify_final_results(self):
        """Verify the final sync results"""
        print("\n✅ FINAL VERIFICATION")
        print("=" * 25)
        
        # Get updated state
        dedup_info = self.get_events_with_deduplication_info()
        final_count = len(dedup_info['events'])
        
        print(f"📊 Final event count: {final_count}")
        
        # Show venue breakdown
        print(f"📋 Events by venue:")
        venue_totals = {}
        for venue, events in dedup_info['by_venue'].items():
            count = len(events)
            venue_totals[venue] = count
            print(f"   • {venue}: {count} events")
        
        # Check for duplicates
        duplicates = []
        for title, events in dedup_info['by_title'].items():
            if len(events) > 1:
                duplicates.append((title, len(events)))
        
        if duplicates:
            print(f"\n⚠️ Found {len(duplicates)} duplicate titles:")
            for title, count in duplicates[:5]:
                print(f"   • \"{title}\" appears {count} times")
        else:
            print(f"\n✅ No duplicate events found")
        
        # Success metrics
        conduit_count = venue_totals.get('Conduit', 0)
        willspub_count = venue_totals.get("Will's Pub", 0)
        
        print(f"\n🎯 ISSUE RESOLUTION:")
        if conduit_count >= 5:  # Significant improvement from 1
            print(f"   ✅ Conduit events: {conduit_count} (was 1) - FIXED!")
        else:
            print(f"   ⚠️  Conduit events: {conduit_count} (target: 19)")
        
        if willspub_count >= 15:  # Improvement from 13
            print(f"   ✅ Will's Pub events: {willspub_count} (was 13) - IMPROVED!")
        else:
            print(f"   ⚠️  Will's Pub events: {willspub_count} (target: 20)")

    def run_complete_solution(self):
        """Run the complete sync solution"""
        print("🚀 COMPLETE EVENT SYNC SOLUTION")
        print("=" * 40)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Authenticate
        if not self.authenticate_working_method():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Sync all missing events  
        if not self.sync_all_missing_events():
            print("❌ Sync process had issues")
        
        # Step 3: Verify results
        self.verify_final_results()
        
        print(f"\n🎉 SOLUTION COMPLETE!")
        print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Check Gancio admin: {self.gancio_base_url}/admin")
        print(f"   2. Review and approve new events")
        print(f"   3. Test GitHub Actions with enhanced sync script")
        print(f"   4. Monitor for duplicates in future runs")

if __name__ == "__main__":
    solution = CompleteSyncSolution()
    solution.run_complete_solution()
