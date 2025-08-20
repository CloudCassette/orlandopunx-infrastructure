#!/usr/bin/env python3
"""
Simple Gancio Duplicate Analysis
================================
Quick and reliable duplicate detection and cleanup
"""

import requests
import json
from collections import defaultdict, Counter
from datetime import datetime

class SimpleDuplicateAnalysis:
    def __init__(self):
        self.gancio_url = "http://localhost:13120"
        self.session = requests.Session()

    def get_events(self):
        """Get all events from Gancio API"""
        try:
            response = self.session.get(f"{self.gancio_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                print(f"✅ Retrieved {len(events)} events from Gancio")
                return events
            else:
                print(f"❌ API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def analyze_duplicates(self, events):
        """Find duplicate events by title"""
        print("\n🔍 DUPLICATE ANALYSIS")
        print("=" * 25)
        
        # Group by title
        title_groups = defaultdict(list)
        for event in events:
            title = event.get('title', '').strip()
            if title:
                title_groups[title].append(event)
        
        # Find duplicates
        duplicates = {}
        total_duplicates = 0
        
        for title, group in title_groups.items():
            if len(group) > 1:
                duplicates[title] = group
                total_duplicates += len(group) - 1  # Keep one, count others as duplicates
        
        print(f"📊 Analysis Results:")
        print(f"   📋 Total events: {len(events)}")
        print(f"   🔴 Duplicate titles: {len(duplicates)}")
        print(f"   🗑️ Events to remove: {total_duplicates}")
        
        return duplicates

    def display_duplicates(self, duplicates):
        """Display duplicate details"""
        if not duplicates:
            print("\n✅ No duplicates found!")
            return []
        
        print(f"\n📋 DUPLICATE DETAILS")
        print("=" * 22)
        
        deletion_list = []
        
        for title, events in duplicates.items():
            print(f"\n🔴 \"{title}\" ({len(events)} copies):")
            
            # Sort by ID to be consistent
            sorted_events = sorted(events, key=lambda x: x.get('id', 0))
            
            for i, event in enumerate(sorted_events):
                event_id = event.get('id')
                place = event.get('place', {})
                place_name = place.get('name', 'Unknown') if isinstance(place, dict) else 'Unknown'
                start_time = event.get('start_datetime', 'Unknown')
                
                if i == 0:
                    print(f"   🟢 KEEP   ID:{event_id} | {place_name} | {start_time}")
                else:
                    print(f"   🔴 DELETE ID:{event_id} | {place_name} | {start_time}")
                    deletion_list.append(event_id)
        
        return deletion_list

    def delete_events(self, event_ids, dry_run=True):
        """Delete events (dry run by default)"""
        if not event_ids:
            print("\n✅ No events to delete")
            return True
        
        mode = "DRY RUN" if dry_run else "LIVE DELETION"
        print(f"\n🗑️ EVENT DELETION ({mode})")
        print("=" * 30)
        
        success_count = 0
        failed_count = 0
        
        for i, event_id in enumerate(event_ids, 1):
            print(f"[{i}/{len(event_ids)}] Processing event ID: {event_id}")
            
            if dry_run:
                print(f"   🧪 [DRY RUN] Would delete event ID: {event_id}")
                success_count += 1
            else:
                try:
                    # Test admin session first
                    admin_check = self.session.get(f"{self.gancio_url}/admin")
                    if admin_check.status_code != 200:
                        print(f"   ❌ Not authenticated for deletion")
                        failed_count += 1
                        continue
                    
                    # Try DELETE request
                    delete_response = self.session.delete(f"{self.gancio_url}/api/event/{event_id}")
                    
                    if delete_response.status_code in [200, 204]:
                        print(f"   ✅ Deleted event ID: {event_id}")
                        success_count += 1
                    else:
                        print(f"   ❌ Failed: HTTP {delete_response.status_code}")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    failed_count += 1
        
        print(f"\n📊 DELETION RESULTS:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        return failed_count == 0

    def backup_events(self, events):
        """Create backup of all events"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"scripts/event-sync/gancio_backup_{timestamp}.json"
        
        try:
            with open(backup_file, 'w') as f:
                json.dump(events, f, indent=2, default=str)
            
            print(f"💾 Backup created: {backup_file}")
            print(f"   📊 Events backed up: {len(events)}")
            return backup_file
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None

    def run_analysis(self, perform_deletion=False):
        """Run complete duplicate analysis"""
        print("🔍 SIMPLE GANCIO DUPLICATE ANALYSIS")
        print("=" * 40)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get events
        events = self.get_events()
        if not events:
            return False
        
        # Create backup
        backup_file = self.backup_events(events)
        
        # Analyze duplicates
        duplicates = self.analyze_duplicates(events)
        deletion_list = self.display_duplicates(duplicates)
        
        if deletion_list:
            print(f"\n💡 Found {len(deletion_list)} events to delete")
            
            if perform_deletion:
                print(f"\n⚠️ WARNING: About to delete {len(deletion_list)} duplicate events!")
                confirm = input("Type 'DELETE' to confirm: ")
                
                if confirm == 'DELETE':
                    success = self.delete_events(deletion_list, dry_run=False)
                    
                    if success:
                        print("\n✅ Cleanup completed successfully!")
                        
                        # Verify results
                        print("\n🔍 Verifying cleanup...")
                        new_events = self.get_events()
                        new_duplicates = self.analyze_duplicates(new_events)
                        
                        if not new_duplicates:
                            print("🎉 SUCCESS: No duplicates remaining!")
                        else:
                            print("⚠️ Some duplicates may still remain")
                    else:
                        print("❌ Cleanup had errors - check results")
                else:
                    print("❌ Cleanup cancelled")
            else:
                print(f"\n💡 This was a dry run. To delete duplicates:")
                print(f"   python3 {__file__} --delete")
        else:
            print("\n✅ No duplicates found - database is clean!")
        
        return True

if __name__ == "__main__":
    import sys
    
    perform_deletion = len(sys.argv) > 1 and sys.argv[1] == '--delete'
    
    analyzer = SimpleDuplicateAnalysis()
    analyzer.run_analysis(perform_deletion)
