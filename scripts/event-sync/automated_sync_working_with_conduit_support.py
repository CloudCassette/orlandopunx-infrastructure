#!/usr/bin/env python3
"""
🤖 Automated Orlando Punk Events Sync - Enhanced with Conduit Support
===================================================================
Uses the same authentication method as the working willspub_to_gancio_final_working.py
but adds proper venue mapping for Conduit and other venues to prevent null place errors.
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import hashlib

# Import our fixed scraper functions
from enhanced_multi_venue_sync import scrape_willspub_events

class EnhancedGancioSync:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        
        # Set headers like the working script
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        self.authenticated = False
        self.venue_mappings = {}  # Will be populated from Gancio
        
    def authenticate(self):
        """Authenticate with Gancio using the WORKING method"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ Missing GANCIO_PASSWORD environment variable")
            print("💡 Make sure you added it to your .bashrc and reloaded your shell")
            return False
        
        print(f"🔑 Authenticating with Gancio as {email}...")
        
        try:
            # Use the WORKING authentication method (web form, not API)
            login_data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Authentication successful!")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def load_venue_mappings(self):
        """Load venue mappings from Gancio places"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/places")
            if response.status_code == 200:
                places = response.json()
                
                # Create venue name -> place_id mapping
                self.venue_mappings = {}
                
                for place in places:
                    name = place.get('name', '').strip()
                    place_id = place.get('id')
                    
                    if name and place_id:
                        # Add exact match
                        self.venue_mappings[name.lower()] = place_id
                        
                        # Add some common variations
                        if name.lower() == "will's pub":
                            self.venue_mappings["wills pub"] = place_id
                            self.venue_mappings["willspub"] = place_id
                        elif name.lower() == "conduit":
                            self.venue_mappings["conduit fl"] = place_id
                            self.venue_mappings["conduit orlando"] = place_id

                print(f"📍 Loaded {len(self.venue_mappings)} venue mappings:")
                for venue, place_id in self.venue_mappings.items():
                    print(f"   • {venue.title()} → ID {place_id}")
                
                return True
            else:
                print(f"❌ Could not load venues: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading venues: {e}")
            return False

    def get_place_id_for_venue(self, venue_name):
        """Get place_id for a venue, with intelligent fallback"""
        if not venue_name:
            return None
        
        venue_lower = venue_name.lower().strip()
        
        # Direct mapping lookup
        if venue_lower in self.venue_mappings:
            return self.venue_mappings[venue_lower]
        
        # Fuzzy matching for common patterns
        for mapped_venue, place_id in self.venue_mappings.items():
            if venue_lower in mapped_venue or mapped_venue in venue_lower:
                print(f"   🎯 Fuzzy match: '{venue_name}' → '{mapped_venue}' (ID {place_id})")
                return place_id
        
        # Pattern-based detection for Conduit events
        conduit_patterns = [
            'conduit', '6700 aloma', 'downtown orlando', 'live music at conduit'
        ]
        
        if any(pattern in venue_lower for pattern in conduit_patterns):
            conduit_id = self.venue_mappings.get('conduit')
            if conduit_id:
                print(f"   🎯 Pattern match for Conduit: '{venue_name}' → ID {conduit_id}")
                return conduit_id
        
        return None

    def ensure_event_has_venue(self, event_data):
        """Ensure event has proper venue assignment"""
        venue_name = event_data.get('venue', '').strip()
        
        # Get place_id for venue
        place_id = self.get_place_id_for_venue(venue_name)
        
        if not place_id:
            # Try to extract venue from other fields
            description = event_data.get('description', '')
            title = event_data.get('title', '')
            
            # Look for venue mentions in description or title
            combined_text = f"{title} {description}".lower()
            
            for mapped_venue, mapped_id in self.venue_mappings.items():
                if mapped_venue in combined_text:
                    place_id = mapped_id
                    venue_name = mapped_venue.title()
                    print(f"   📍 Detected venue from content: {venue_name} (ID {place_id})")
                    break
        
        if not place_id:
            # Default to Will's Pub as fallback (safest option)
            default_id = self.venue_mappings.get("will's pub", 1)
            print(f"   ⚠️  No venue detected for '{event_data.get('title', 'Unknown')}', using default venue (ID {default_id})")
            place_id = default_id
            venue_name = "Will's Pub"
        
        # Update event data with proper venue info
        event_data['venue'] = venue_name
        event_data['place_id'] = place_id
        
        return event_data

    def create_event_in_gancio(self, event_data):
        """Create event in Gancio with proper venue assignment"""
        if not self.authenticated:
            print("   ❌ Not authenticated")
            return False
        
        # CRITICAL: Ensure event has proper venue assignment
        event_data = self.ensure_event_has_venue(event_data)
        
        # Convert date/time to timestamp
        try:
            event_datetime = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
            start_timestamp = int(event_datetime.timestamp())
        except:
            print(f"   ❌ Invalid date/time format for {event_data.get('title', 'Unknown')}")
            return False
        
        end_timestamp = start_timestamp + (3 * 3600)  # 3 hours later
        
        # Build Gancio event data with proper venue
        gancio_data = {
            'title': event_data['title'],
            'description': event_data.get('description', ''),
            'start_datetime': start_timestamp,
            'end_datetime': end_timestamp,
            'place_id': event_data['place_id'],  # This should never be None now
            'tags': [event_data['venue'].lower().replace("'", "")]
        }
        
        try:
            response = self.session.post(f"{self.gancio_base_url}/api/event", json=gancio_data)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ {event_data['title']} → {event_data['venue']} (ID {event_data['place_id']})")
                return True
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error creating event: {e}")
            return False

def scrape_conduit_events_basic():
    """Basic Conduit event extraction (fallback if conduit_scraper not available)"""
    # This is a simplified version - you might want to import from your conduit_scraper
    # For now, just return empty list as fallback
    try:
        from conduit_scraper import scrape_conduit_events
        print("📥 Scraping Conduit events...")
        events = scrape_conduit_events(download_images=False)
        
        # Ensure all Conduit events have proper venue assignment
        for event in events:
            if not event.get('venue'):
                event['venue'] = 'Conduit'
        
        return events
    except ImportError:
        print("ℹ️  Conduit scraper not available, skipping Conduit events")
        return []
    except Exception as e:
        print(f"⚠️  Error scraping Conduit events: {e}")
        return []

def main():
    """Main automated sync function with enhanced venue support"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("🤖 ENHANCED MULTI-VENUE AUTOMATED SYNC")
    print("="*50)
    print(f"⏰ Started: {timestamp}")
    
    # Initialize syncer
    syncer = EnhancedGancioSync()
    
    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed. Exiting.")
        return 1
    
    # Load venue mappings
    if not syncer.load_venue_mappings():
        print("❌ Could not load venue mappings. Exiting.")
        return 1
    
    # Scrape events from multiple sources
    all_events = []
    
    # Will's Pub events
    print("📥 Scraping Will's Pub events...")
    willspub_events = scrape_willspub_events()
    if willspub_events:
        all_events.extend(willspub_events)
        print(f"   ✅ Found {len(willspub_events)} Will's Pub events")
    
    # Conduit events
    conduit_events = scrape_conduit_events_basic()
    if conduit_events:
        all_events.extend(conduit_events)
        print(f"   ✅ Found {len(conduit_events)} Conduit events")
    
    if not all_events:
        print("📭 No events found from any source")
        return 0
    
    print(f"📋 Total events from all sources: {len(all_events)}")
    
    # Get existing events to avoid duplicates  
    try:
        response = syncer.session.get(f"{syncer.gancio_base_url}/api/events")
        if response.status_code == 200:
            existing_events = {event['title'] for event in response.json()}
            print(f"📊 Current Gancio events: {len(existing_events)}")
        else:
            existing_events = set()
            print("⚠️  Could not fetch existing events")
    except:
        existing_events = set()
        print("⚠️  Could not fetch existing events")
    
    # Filter for new events only
    new_events = [event for event in all_events if event['title'] not in existing_events]
    
    print(f"🆕 New events to sync: {len(new_events)}")
    print(f"♻️  Existing events skipped: {len(all_events) - len(new_events)}")
    
    if not new_events:
        print("✨ All events already exist - no work to do!")
        return 0
    
    # Submit new events with venue validation
    print(f"🚀 Submitting {len(new_events)} new events with venue enforcement...")
    
    submitted = 0
    for event in new_events:
        if syncer.create_event_in_gancio(event):
            submitted += 1
    
    print(f"✨ Sync complete: {submitted}/{len(new_events)} events submitted")
    
    # Venue summary
    print("\n📍 Venue Summary:")
    venue_counts = {}
    for event in new_events[:submitted]:  # Only count successfully submitted events
        venue = event.get('venue', 'Unknown')
        venue_counts[venue] = venue_counts.get(venue, 0) + 1
    
    for venue, count in venue_counts.items():
        print(f"   • {venue}: {count} events")
    
    # Log summary
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"⏰ Completed: {end_time}")
    
    return 0 if submitted > 0 or len(new_events) == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
