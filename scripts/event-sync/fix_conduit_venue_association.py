#!/usr/bin/env python3
"""
Fix Conduit Venue Association Issues
===================================

This script identifies and fixes Conduit events that have null/missing venue associations
in Gancio, which causes admin panel errors.
"""

import requests
import json
import os
from datetime import datetime

class ConduitVenueFixer:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        })
        self.authenticated = False
        self.places = {}

    def test_gancio_connection(self):
        """Test basic Gancio connectivity"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/")
            if response.status_code == 200:
                print("✅ Gancio is accessible")
                return True
            else:
                print(f"❌ Gancio HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Gancio connection failed: {e}")
            return False

    def authenticate(self):
        """Authenticate with Gancio"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ GANCIO_PASSWORD environment variable not set")
            print("   Please set: export GANCIO_PASSWORD='your_password'")
            return False
        
        try:
            response = self.session.post(f"{self.gancio_base_url}/auth/login", 
                                       data={'email': email, 'password': password})
            
            if response.status_code == 302 or 'admin' in response.url:
                self.authenticated = True
                print("✅ Authenticated with Gancio")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_places(self):
        """Get all places/venues from Gancio"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/places")
            if response.status_code == 200:
                places = response.json()
                
                # Create name -> ID mapping
                self.places = {}
                for place in places:
                    name = place.get('name', '').strip()
                    place_id = place.get('id')
                    self.places[name.lower()] = {
                        'id': place_id,
                        'name': name,
                        'address': place.get('address', '')
                    }
                
                print(f"📍 Found {len(places)} venues:")
                for name, info in self.places.items():
                    print(f"   • {info['name']} (ID: {info['id']})")
                
                return places
            else:
                print(f"❌ Could not fetch places: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching places: {e}")
            return []

    def get_events_with_venue_issues(self):
        """Find events with null/missing venue associations"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code != 200:
                print(f"❌ Could not fetch events: HTTP {response.status_code}")
                return []
            
            events = response.json()
            print(f"📊 Checking {len(events)} events for venue issues...")
            
            problematic_events = []
            conduit_events_without_venue = []
            
            for event in events:
                event_id = event.get('id')
                title = event.get('title', 'Untitled')
                place = event.get('place')
                place_id = event.get('placeId')
                
                # Check for venue issues
                has_venue_issue = (
                    place is None or 
                    place_id is None or 
                    place_id == 0 or
                    (isinstance(place, dict) and not place.get('name'))
                )
                
                if has_venue_issue:
                    problematic_events.append(event)
                    
                    # Special check for Conduit events
                    if self.is_likely_conduit_event(event):
                        conduit_events_without_venue.append(event)
                        print(f"🎯 Conduit event without venue: ID {event_id} - {title}")
            
            print(f"\n📋 Venue Issue Summary:")
            print(f"   • Total events with venue issues: {len(problematic_events)}")
            print(f"   • Conduit events without venue: {len(conduit_events_without_venue)}")
            
            return problematic_events, conduit_events_without_venue
            
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return [], []

    def is_likely_conduit_event(self, event):
        """Determine if an event is likely a Conduit event"""
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        
        conduit_indicators = [
            'conduit',
            'live music at conduit',
            '6700 aloma',
            '6700 aloma ave',
            'downtown orlando'
        ]
        
        content = f"{title} {description}"
        return any(indicator in content for indicator in conduit_indicators)

    def get_conduit_place_id(self):
        """Get the Conduit place ID"""
        for name, info in self.places.items():
            if 'conduit' in name:
                return info['id'], info['name']
        
        print("❌ Conduit venue not found in places")
        print("   Available venues:", list(self.places.keys()))
        return None, None

    def fix_conduit_venue_associations(self, conduit_events, dry_run=True):
        """Fix venue associations for Conduit events"""
        if not conduit_events:
            print("✅ No Conduit events need venue fixing")
            return True
        
        conduit_place_id, conduit_name = self.get_conduit_place_id()
        if not conduit_place_id:
            print("❌ Cannot fix - Conduit venue not found")
            return False
        
        print(f"\n🔧 {'DRY RUN - ' if dry_run else ''}Fixing {len(conduit_events)} Conduit events...")
        print(f"   Will assign to: {conduit_name} (ID: {conduit_place_id})")
        
        fixed_count = 0
        
        for event in conduit_events:
            event_id = event.get('id')
            title = event.get('title', 'Untitled')
            
            if dry_run:
                print(f"   📝 Would fix: ID {event_id} - {title}")
                fixed_count += 1
            else:
                success = self.update_event_venue(event_id, conduit_place_id, title)
                if success:
                    fixed_count += 1
        
        if dry_run:
            print(f"\n🔍 DRY RUN COMPLETE: Would fix {fixed_count} events")
            print("   Run with --fix to actually update the events")
        else:
            print(f"\n✅ FIXED: {fixed_count} events updated successfully")
        
        return True

    def update_event_venue(self, event_id, place_id, title):
        """Update an event's venue association"""
        try:
            # Get the full event data first
            response = self.session.get(f"{self.gancio_base_url}/api/event/{event_id}")
            if response.status_code != 200:
                print(f"   ❌ Could not fetch event {event_id}: HTTP {response.status_code}")
                return False
            
            event_data = response.json()
            
            # Update the place association
            event_data['placeId'] = place_id
            
            # Update the event
            response = self.session.put(f"{self.gancio_base_url}/api/event/{event_id}", 
                                       json=event_data)
            
            if response.status_code == 200:
                print(f"   ✅ Fixed: ID {event_id} - {title}")
                return True
            else:
                print(f"   ❌ Failed to update event {event_id}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error updating event {event_id}: {e}")
            return False

    def generate_manual_fix_commands(self, conduit_events):
        """Generate manual SQL/curl commands as backup"""
        conduit_place_id, conduit_name = self.get_conduit_place_id()
        if not conduit_place_id:
            return
        
        print(f"\n🔧 Manual Fix Commands (as backup):")
        print("="*50)
        
        print("\n# SQL Commands (if you have direct database access):")
        for event in conduit_events:
            event_id = event.get('id')
            title = event.get('title', 'Untitled').replace("'", "''")  # Escape quotes
            print(f"UPDATE events SET placeId = {conduit_place_id} WHERE id = {event_id}; -- {title}")
        
        print("\n# Curl Commands (alternative API approach):")
        for event in conduit_events:
            event_id = event.get('id')
            title = event.get('title', 'Untitled')
            print(f"# Fix: {title}")
            print(f"curl -X PUT http://localhost:13120/api/event/{event_id} \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  -d '{{\"placeId\": {conduit_place_id}}}'")
            print()

def main():
    import sys
    
    print("🔧 CONDUIT VENUE ASSOCIATION FIXER")
    print("="*40)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse arguments
    dry_run = '--fix' not in sys.argv
    show_commands = '--generate-commands' in sys.argv
    
    if dry_run and not show_commands:
        print("🔍 Running in DRY RUN mode (no changes will be made)")
        print("   Use --fix to actually fix the issues")
        print("   Use --generate-commands to show manual fix commands")
    
    fixer = ConduitVenueFixer()
    
    # Step 1: Test connection
    if not fixer.test_gancio_connection():
        print("❌ Cannot connect to Gancio. Is it running?")
        return 1
    
    # Step 2: Authenticate
    if not fixer.authenticate():
        print("❌ Authentication failed. Cannot proceed with fixes.")
        return 1
    
    # Step 3: Get venues
    places = fixer.get_places()
    if not places:
        print("❌ Could not fetch venues")
        return 1
    
    # Step 4: Find problematic events
    all_problematic, conduit_events = fixer.get_events_with_venue_issues()
    
    if not all_problematic:
        print("✅ No events with venue issues found!")
        return 0
    
    # Step 5: Show manual commands if requested
    if show_commands:
        fixer.generate_manual_fix_commands(conduit_events)
        return 0
    
    # Step 6: Fix Conduit venue associations
    success = fixer.fix_conduit_venue_associations(conduit_events, dry_run=dry_run)
    
    if success and conduit_events:
        if dry_run:
            print(f"\n💡 To actually fix these {len(conduit_events)} Conduit events:")
            print(f"   python3 {sys.argv[0]} --fix")
            print(f"\n💡 To see manual fix commands:")
            print(f"   python3 {sys.argv[0]} --generate-commands")
        else:
            print(f"\n🎉 Successfully fixed venue associations!")
            print(f"   The admin panel errors should now be resolved.")
            print(f"   You can verify by checking the events in Gancio admin.")
    
    return 0

if __name__ == "__main__":
    exit(main())
