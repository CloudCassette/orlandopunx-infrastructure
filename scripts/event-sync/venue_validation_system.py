#!/usr/bin/env python3
"""
Venue Validation and Data Integrity System
Handles venue validation, fixing null venue data, and ensuring data consistency
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class VenueValidationSystem:
    def __init__(self, gancio_base_url="http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()
        self.venue_mappings = {
            # Venue name variations to standard venue info
            "will's pub": {"id": 1, "name": "Will's Pub", "address": "1042 N. Mills Ave. Orlando, FL 32803"},
            "wills pub": {"id": 1, "name": "Will's Pub", "address": "1042 N. Mills Ave. Orlando, FL 32803"},
            "conduit": {"id": 2, "name": "Conduit", "address": "22 S Magnolia Ave, Orlando, FL 32801"},
            "stardust": {"id": 4, "name": "Stardust Video & Coffee", "address": "1842 Winter Park Rd"},
            "stardust video & coffee": {"id": 4, "name": "Stardust Video & Coffee", "address": "1842 Winter Park Rd"},
            "sly fox": {"id": 5, "name": "Sly Fox", "address": "Not Available"},
        }
        self.default_venue = {"id": 1, "name": "Will's Pub", "address": "1042 N. Mills Ave. Orlando, FL 32803"}
        
    def authenticate(self):
        """Authenticate with Gancio"""
        print("🔑 Authenticating with Gancio...")
        
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False
            
        try:
            # Get login page first
            self.session.get(f"{self.gancio_base_url}/login")
            
            # Post login credentials
            login_url = f"{self.gancio_base_url}/auth/login"
            response = self.session.post(login_url, data={
                'email': email,
                'password': password
            }, allow_redirects=True)
            
            if 'admin' in response.url or response.status_code == 200:
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_all_events(self) -> List[Dict]:
        """Get all events from Gancio"""
        try:
            response = requests.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to fetch events: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []
    
    def analyze_venue_data(self) -> Dict:
        """Analyze venue data integrity"""
        print("🔍 Analyzing venue data integrity...")
        
        events = self.get_all_events()
        if not events:
            return {}
        
        analysis = {
            'total_events': len(events),
            'events_with_null_place': [],
            'events_with_null_place_name': [],
            'events_with_empty_place_name': [],
            'events_with_invalid_place_id': [],
            'venue_distribution': {},
            'venue_id_mapping': {}
        }
        
        for event in events:
            event_id = event.get('id')
            title = event.get('title', 'No title')
            place = event.get('place')
            place_id = event.get('placeId')
            
            # Check for null place
            if place is None:
                analysis['events_with_null_place'].append({
                    'id': event_id, 'title': title, 'placeId': place_id
                })
                continue
            
            # Check for null place name
            place_name = place.get('name') if place else None
            if place_name is None:
                analysis['events_with_null_place_name'].append({
                    'id': event_id, 'title': title, 'place': place, 'placeId': place_id
                })
                continue
            
            # Check for empty place name
            if place_name == "":
                analysis['events_with_empty_place_name'].append({
                    'id': event_id, 'title': title, 'place': place, 'placeId': place_id
                })
                continue
            
            # Check for invalid place ID
            if place_id is None or place_id == 0:
                analysis['events_with_invalid_place_id'].append({
                    'id': event_id, 'title': title, 'place': place, 'placeId': place_id
                })
            
            # Count venue distribution
            if place_name not in analysis['venue_distribution']:
                analysis['venue_distribution'][place_name] = 0
            analysis['venue_distribution'][place_name] += 1
            
            # Map venue names to IDs
            if place_name not in analysis['venue_id_mapping']:
                analysis['venue_id_mapping'][place_name] = place.get('id')
        
        return analysis
    
    def normalize_venue_name(self, venue_name: str) -> str:
        """Normalize venue name for lookup"""
        if not venue_name:
            return ""
        return venue_name.strip().lower()
    
    def get_venue_info(self, venue_name: str) -> Dict:
        """Get venue info from mapping or return default"""
        normalized = self.normalize_venue_name(venue_name)
        return self.venue_mappings.get(normalized, self.default_venue)
    
    def validate_event_venue(self, event: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate event venue data
        Returns: (is_valid, issue_description, suggested_fix)
        """
        place = event.get('place')
        place_id = event.get('placeId')
        
        if place is None:
            return False, "place_is_null", self.default_venue
        
        if not isinstance(place, dict):
            return False, "place_not_object", self.default_venue
        
        place_name = place.get('name')
        if place_name is None:
            return False, "place_name_is_null", self.default_venue
        
        if place_name == "":
            return False, "place_name_is_empty", self.default_venue
        
        if place_id is None or place_id == 0:
            # Try to get correct place_id from venue mapping
            venue_info = self.get_venue_info(place_name)
            return False, "place_id_invalid", venue_info
        
        return True, "venue_valid", None
    
    def fix_event_venue(self, event_id: int, venue_info: Dict) -> bool:
        """Fix event venue data"""
        if not self.authenticate():
            return False
        
        try:
            update_url = f"{self.gancio_base_url}/api/event/{event_id}"
            update_data = {
                'place_id': venue_info['id']
            }
            
            response = self.session.put(update_url, json=update_data)
            
            if response.status_code in [200, 204]:
                print(f"✅ Fixed venue for event {event_id}")
                return True
            else:
                print(f"❌ Failed to fix venue for event {event_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error fixing venue for event {event_id}: {e}")
            return False
    
    def run_venue_validation(self, fix_issues=False) -> Dict:
        """Run comprehensive venue validation"""
        print("🚀 Starting venue validation...")
        
        analysis = self.analyze_venue_data()
        
        print(f"\n📊 Venue Data Analysis:")
        print(f"   Total events: {analysis['total_events']}")
        print(f"   Events with null place: {len(analysis['events_with_null_place'])}")
        print(f"   Events with null place name: {len(analysis['events_with_null_place_name'])}")
        print(f"   Events with empty place name: {len(analysis['events_with_empty_place_name'])}")
        print(f"   Events with invalid place ID: {len(analysis['events_with_invalid_place_id'])}")
        
        if analysis['venue_distribution']:
            print(f"\n🏢 Venue Distribution:")
            for venue, count in sorted(analysis['venue_distribution'].items()):
                venue_id = analysis['venue_id_mapping'].get(venue, 'Unknown')
                print(f"   {venue} (ID: {venue_id}): {count} events")
        
        # Report issues
        issues = []
        
        for issue_type in ['events_with_null_place', 'events_with_null_place_name', 
                          'events_with_empty_place_name', 'events_with_invalid_place_id']:
            if analysis[issue_type]:
                issues.extend(analysis[issue_type])
                print(f"\n⚠️ {issue_type.replace('_', ' ').title()}:")
                for event in analysis[issue_type]:
                    print(f"   Event {event['id']}: {event['title'][:50]}...")
        
        if fix_issues and issues:
            print(f"\n🔧 Attempting to fix {len(issues)} venue issues...")
            fixed_count = 0
            
            for issue_event in issues:
                event_id = issue_event['id']
                # Get suggested venue info
                venue_info = self.default_venue  # Could be more intelligent based on event content
                
                if self.fix_event_venue(event_id, venue_info):
                    fixed_count += 1
            
            print(f"✅ Fixed {fixed_count}/{len(issues)} venue issues")
        
        return analysis
    
    def create_venue_report(self, analysis: Dict):
        """Create detailed venue report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"venue_validation_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"📄 Detailed venue report saved to: {report_file}")
        return report_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Venue Validation System')
    parser.add_argument('--analyze', action='store_true', help='Analyze venue data')
    parser.add_argument('--fix', action='store_true', help='Fix venue issues')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    
    args = parser.parse_args()
    
    validator = VenueValidationSystem()
    
    if args.analyze or args.fix or args.report:
        analysis = validator.run_venue_validation(fix_issues=args.fix)
        
        if args.report:
            validator.create_venue_report(analysis)
    else:
        print("Use --analyze to check venue data, --fix to repair issues, --report for detailed report")

if __name__ == "__main__":
    main()
