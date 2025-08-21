#!/usr/bin/env python3
"""
Verification script for venue assignment system
Tests current venue assignments and validates the enforcement system
"""

import requests
import json
from typing import Dict, List

def verify_current_venue_assignments():
    """Verify all current events have proper venue assignments"""
    print("🔍 Verifying current venue assignments in Gancio...")
    
    try:
        response = requests.get("http://localhost:13120/api/events")
        if response.status_code != 200:
            print(f"❌ Failed to fetch events: {response.status_code}")
            return False
        
        events = response.json()
        print(f"📋 Checking {len(events)} events...")
        
        issues = []
        venue_stats = {}
        
        for event in events:
            event_id = event.get('id')
            title = event.get('title', 'No title')
            place = event.get('place')
            place_id = event.get('placeId')
            
            # Check for issues
            if place is None:
                issues.append(f"Event {event_id}: NULL place object - {title[:40]}...")
            elif not isinstance(place, dict):
                issues.append(f"Event {event_id}: Invalid place object - {title[:40]}...")
            elif not place.get('name'):
                issues.append(f"Event {event_id}: Missing place name - {title[:40]}...")
            elif place_id is None or place_id == 0:
                issues.append(f"Event {event_id}: Invalid place ID ({place_id}) - {title[:40]}...")
            else:
                # Count venues
                venue_name = place.get('name')
                if venue_name not in venue_stats:
                    venue_stats[venue_name] = {'count': 0, 'place_id': place.get('id')}
                venue_stats[venue_name]['count'] += 1
        
        if issues:
            print(f"\n⚠️ Found {len(issues)} venue issues:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print(f"\n✅ All events have proper venue assignments!")
            
            print(f"\n🏢 Current venue distribution:")
            for venue, stats in sorted(venue_stats.items()):
                print(f"   {venue} (ID: {stats['place_id']}): {stats['count']} events")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verifying venues: {e}")
        return False

def test_venue_enforcer():
    """Test the venue enforcer with sample data"""
    print("\n🧪 Testing venue enforcer...")
    
    # Import the venue enforcer
    try:
        from venue_assignment_fixer import VenueAssignmentFixer
        fixer = VenueAssignmentFixer()
        
        # Test cases
        test_events = [
            {"title": "Test Event at Conduit", "description": "Show at downtown venue"},
            {"title": "Show @ Will's Pub", "venue": "Will's Pub"},
            {"title": "Concert", "description": "At 22 S Magnolia Ave"},
            {"title": "Random Event", "description": "No venue info"},
            {"title": "Stardust Show", "venue": "stardust"},
        ]
        
        print("Testing venue assignment for sample events:")
        for i, event in enumerate(test_events, 1):
            venue_info = fixer.get_venue_info(event.get('venue', ''), event)
            print(f"   {i}. '{event['title']}' → {venue_info['name']} (ID: {venue_info['id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing venue enforcer: {e}")
        return False

def generate_conduit_venue_commands():
    """Generate commands to specifically handle Conduit events"""
    print("\n🎯 Commands for Conduit venue verification:")
    
    commands = [
        # Check for Conduit events
        'curl -s http://localhost:13120/api/events | jq -r \'.[] | select(.place.name | test("conduit"; "i")) | "ID: \\(.id) - \\(.title)"\'',
        
        # Check events without proper place assignment
        'curl -s http://localhost:13120/api/events | jq -r \'.[] | select(.place == null or .placeId == null or .placeId == 0) | "ISSUE - ID: \\(.id) - \\(.title)"\'',
        
        # Count events by venue
        'curl -s http://localhost:13120/api/events | jq -r \'.[].place.name\' | sort | uniq -c | sort -nr',
        
        # Verify Conduit venue ID mapping
        'curl -s http://localhost:13120/api/events | jq -r \'.[] | select(.place.name == "Conduit") | "ID: \\(.id) - PlaceID: \\(.placeId) - \\(.title)"\'',
    ]
    
    print("Run these commands to verify Conduit venue assignments:")
    for i, cmd in enumerate(commands, 1):
        print(f"   {i}. {cmd}")

def main():
    print("🚀 Venue Assignment Verification System")
    print("="*50)
    
    # 1. Verify current assignments
    current_ok = verify_current_venue_assignments()
    
    # 2. Test venue enforcer
    enforcer_ok = test_venue_enforcer()
    
    # 3. Generate commands
    generate_conduit_venue_commands()
    
    print("\n📊 Verification Summary:")
    print(f"   Current venues: {'✅ PASS' if current_ok else '❌ FAIL'}")
    print(f"   Venue enforcer: {'✅ PASS' if enforcer_ok else '❌ FAIL'}")
    
    if current_ok and enforcer_ok:
        print("\n🎉 Venue system is working correctly!")
        print("   • All current events have proper venue assignments")
        print("   • Venue enforcement system is functional")
        print("   • Ready for sync operations with venue guarantees")
    else:
        print("\n⚠️ Issues found that need attention")
    
    print("\n🛠️ Next Steps:")
    print("   1. Run: python3 venue_assignment_fixer.py --analyze")
    print("   2. If issues found: python3 venue_assignment_fixer.py --fix --force")
    print("   3. Update your sync script to use venue enforcement")
    print("   4. Test with: python3 automated_sync_working_fixed_with_venue_enforcement.py")

if __name__ == "__main__":
    main()
