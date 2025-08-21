#!/usr/bin/env python3
"""
Gancio Duplicate Event Cleanup Tool
===================================
Identifies, analyzes, and safely removes duplicate events from Gancio
"""

import requests
import json
import sys
from datetime import datetime
from collections import defaultdict, Counter
import hashlib
import time

class GancioDuplicateCleanup:
    def __init__(self):
        self.gancio_base_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.authenticated = False

    def authenticate(self):
        """Authenticate with Gancio admin"""
        try:
            # Test admin access (should work based on previous success)
            admin_response = self.session.get(f"{self.gancio_base_url}/admin")
            if admin_response.status_code == 200:
                self.authenticated = True
                return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
        return False

    def get_all_events(self):
        """Get all events from Gancio with detailed information"""
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                print(f"✅ Retrieved {len(events)} events from Gancio")
                return events
            else:
                print(f"❌ Failed to get events: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting events: {e}")
            return []

    def analyze_duplicates(self, events):
        """Comprehensive duplicate analysis"""
        print("\n🔍 DUPLICATE ANALYSIS")
        print("=" * 25)
        
        # Different duplicate detection strategies
        duplicate_groups = {
            'exact_title': defaultdict(list),
            'title_hash': defaultdict(list),
            'title_date': defaultdict(list),
            'title_venue': defaultdict(list),
            'fuzzy_match': defaultdict(list)
        }
        
        for event in events:
            event_id = event.get('id')
            title = event.get('title', '').strip()
            start_date = event.get('start_datetime', '')
            place = event.get('place', {})
            place_name = place.get('name', 'Unknown') if isinstance(place, dict) else str(place)
            
            # Strategy 1: Exact title match
            duplicate_groups['exact_title'][title].append(event)
            
            # Strategy 2: Title hash (case-insensitive, whitespace normalized)
            title_normalized = ' '.join(title.lower().split())
            title_hash = hashlib.md5(title_normalized.encode()).hexdigest()
            duplicate_groups['title_hash'][title_hash].append(event)
            
            # Strategy 3: Title + Date combination
            date_key = f"{title}|{str(start_date)[:10]}" if start_date else f"{title}|no_date"
            duplicate_groups['title_date'][date_key].append(event)
            
            # Strategy 4: Title + Venue combination
            venue_key = f"{title}|{place_name}"
            duplicate_groups['title_venue'][venue_key].append(event)
        
        # Find actual duplicates
        duplicates_found = {}
        
        for strategy, groups in duplicate_groups.items():
            strategy_duplicates = []
            for key, group_events in groups.items():
                if len(group_events) > 1:
                    strategy_duplicates.append({
                        'key': key,
                        'events': group_events,
                        'count': len(group_events)
                    })
            duplicates_found[strategy] = strategy_duplicates
        
        return duplicates_found

    def display_duplicates(self, duplicates_found):
        """Display duplicate analysis results"""
        print("\n📊 DUPLICATE DETECTION RESULTS")
        print("=" * 35)
        
        total_duplicates = 0
        recommended_deletions = []
        
        for strategy, duplicates in duplicates_found.items():
            if duplicates:
                print(f"\n🔍 {strategy.upper()} Strategy:")
                print(f"   Found {len(duplicates)} duplicate groups")
                
                for dup_group in duplicates:
                    group_events = dup_group['events']
                    count = dup_group['count']
                    total_duplicates += count - 1  # Keep one, delete others
                    
                    # Show first few examples
                    if strategy == 'exact_title' and len(duplicates) <= 10:
                        key = dup_group['key']
                        print(f"   📋 \"{key}\" ({count} copies):")
                        
                        # Sort by ID to keep oldest/newest consistently
                        sorted_events = sorted(group_events, key=lambda x: x.get('id', 0))
                        
                        for i, event in enumerate(sorted_events):
                            event_id = event.get('id')
                            created = event.get('createdAt', 'Unknown')[:10]
                            place = event.get('place', {})
                            place_name = place.get('name', 'Unknown') if isinstance(place, dict) else str(place)
                            
                            marker = "🟢 KEEP" if i == 0 else "🔴 DELETE"
                            print(f"      {marker} ID:{event_id} | {place_name} | Created:{created}")
                            
                            if i > 0:  # Mark for deletion (keep first one)
                                recommended_deletions.append({
                                    'id': event_id,
                                    'title': key,
                                    'reason': f'Duplicate of ID:{sorted_events[0].get("id")}'
                                })
        
        print(f"\n📊 SUMMARY:")
        print(f"   🔴 Total duplicate events to remove: {total_duplicates}")
        print(f"   💾 Events recommended for deletion: {len(recommended_deletions)}")
        
        return recommended_deletions

    def delete_event_safely(self, event_id, dry_run=True):
        """Safely delete a single event"""
        if dry_run:
            print(f"   🧪 [DRY RUN] Would delete event ID: {event_id}")
            return True
        
        try:
            # Try DELETE API endpoint
            delete_response = self.session.delete(f"{self.gancio_base_url}/api/event/{event_id}")
            
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Deleted event ID: {event_id}")
                return True
            else:
                print(f"   ❌ Failed to delete ID {event_id}: HTTP {delete_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error deleting event ID {event_id}: {e}")
            return False

    def bulk_cleanup_duplicates(self, recommended_deletions, dry_run=True):
        """Perform bulk cleanup of duplicate events"""
        mode = "DRY RUN" if dry_run else "LIVE DELETION"
        print(f"\n🗑️ BULK DUPLICATE CLEANUP ({mode})")
        print("=" * 40)
        
        if not recommended_deletions:
            print("✅ No duplicates found to clean up!")
            return True
        
        print(f"📋 Processing {len(recommended_deletions)} duplicate events...")
        
        success_count = 0
        failed_count = 0
        
        for i, deletion in enumerate(recommended_deletions, 1):
            event_id = deletion['id']
            title = deletion['title']
            reason = deletion['reason']
            
            print(f"\n[{i}/{len(recommended_deletions)}] Processing: \"{title[:50]}...\"")
            print(f"   Event ID: {event_id}")
            print(f"   Reason: {reason}")
            
            if self.delete_event_safely(event_id, dry_run):
                success_count += 1
            else:
                failed_count += 1
            
            # Rate limiting
            if not dry_run:
                time.sleep(0.5)
        
        print(f"\n📊 CLEANUP RESULTS:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📊 Success Rate: {(success_count/(success_count+failed_count)*100):.1f}%" if (success_count + failed_count) > 0 else "N/A")
        
        return failed_count == 0

    def verify_cleanup_results(self):
        """Verify that duplicates have been removed"""
        print(f"\n✅ POST-CLEANUP VERIFICATION")
        print("=" * 30)
        
        # Re-fetch events
        events = self.get_all_events()
        if not events:
            print("❌ Could not verify - unable to fetch events")
            return False
        
        # Re-run duplicate analysis
        duplicates_found = self.analyze_duplicates(events)
        
        remaining_duplicates = 0
        for strategy, duplicates in duplicates_found.items():
            if strategy == 'exact_title':  # Focus on main strategy
                for dup_group in duplicates:
                    if dup_group['count'] > 1:
                        remaining_duplicates += dup_group['count'] - 1
        
        print(f"📊 Verification Results:")
        print(f"   📋 Total events: {len(events)}")
        print(f"   🔴 Remaining duplicates: {remaining_duplicates}")
        
        if remaining_duplicates == 0:
            print("   🎉 SUCCESS: No duplicates found!")
            return True
        else:
            print("   ⚠️  Some duplicates may remain")
            return False

    def generate_prevention_script(self):
        """Generate script to prevent future duplicates"""
        prevention_script = '''#!/usr/bin/env python3
"""
Duplicate Prevention for Future Syncs
====================================
Enhanced deduplication logic for event sync scripts
"""

import hashlib
from collections import defaultdict

class DuplicatePrevention:
    def __init__(self):
        self.existing_events = {}
        self.title_hashes = set()
    
    def load_existing_events(self, gancio_events):
        """Load existing events for deduplication"""
        self.existing_events = {}
        self.title_hashes = set()
        
        for event in gancio_events:
            title = event.get('title', '').strip()
            event_id = event.get('id')
            
            # Store by exact title
            self.existing_events[title] = event_id
            
            # Store normalized hash
            title_normalized = ' '.join(title.lower().split())
            title_hash = hashlib.md5(title_normalized.encode()).hexdigest()
            self.title_hashes.add(title_hash)
    
    def is_duplicate(self, new_event_title):
        """Check if event is a duplicate"""
        title = new_event_title.strip()
        
        # Exact match check
        if title in self.existing_events:
            return True, f"Exact title match with ID: {self.existing_events[title]}"
        
        # Fuzzy match check
        title_normalized = ' '.join(title.lower().split())
        title_hash = hashlib.md5(title_normalized.encode()).hexdigest()
        
        if title_hash in self.title_hashes:
            return True, "Fuzzy title match (normalized)"
        
        return False, None
    
    def add_new_event(self, event_title, event_id):
        """Add newly created event to tracking"""
        title = event_title.strip()
        self.existing_events[title] = event_id
        
        title_normalized = ' '.join(title.lower().split())
        title_hash = hashlib.md5(title_normalized.encode()).hexdigest()
        self.title_hashes.add(title_hash)

# Usage example in sync scripts:
"""
# At start of sync
dup_prevention = DuplicatePrevention()
existing_gancio_events = get_gancio_events()  # Your API call
dup_prevention.load_existing_events(existing_gancio_events)

# Before creating each event
is_dup, reason = dup_prevention.is_duplicate(event_title)
if is_dup:
    print(f"⚠️ Skipping duplicate: {event_title} ({reason})")
    continue

# After successfully creating event
dup_prevention.add_new_event(event_title, new_event_id)
"""
'''
        
        with open("scripts/event-sync/duplicate_prevention.py", "w") as f:
            f.write(prevention_script)
        
        print(f"✅ Created duplicate prevention script: scripts/event-sync/duplicate_prevention.py")

    def run_complete_cleanup(self, dry_run=True):
        """Run complete duplicate cleanup process"""
        mode = "DRY RUN MODE" if dry_run else "LIVE CLEANUP MODE"
        print(f"🧹 GANCIO DUPLICATE CLEANUP - {mode}")
        print("=" * 50)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return False
        
        # Step 2: Get all events
        events = self.get_all_events()
        if not events:
            print("❌ No events found - nothing to clean")
            return False
        
        # Step 3: Analyze duplicates
        duplicates_found = self.analyze_duplicates(events)
        
        # Step 4: Display and get recommendations
        recommended_deletions = self.display_duplicates(duplicates_found)
        
        # Step 5: Perform cleanup
        if recommended_deletions:
            if dry_run:
                print(f"\n💡 This was a DRY RUN. To perform actual cleanup:")
                print(f"   python3 {sys.argv[0]} --live")
            else:
                # Confirm before live deletion
                print(f"\n⚠️ WARNING: About to delete {len(recommended_deletions)} events!")
                confirm = input("Type 'DELETE' to confirm: ")
                if confirm == 'DELETE':
                    self.bulk_cleanup_duplicates(recommended_deletions, dry_run=False)
                    
                    # Step 6: Verify cleanup
                    self.verify_cleanup_results()
                else:
                    print("❌ Cleanup cancelled by user")
                    return False
        
        # Step 7: Generate prevention tools
        self.generate_prevention_script()
        
        print(f"\n🏁 CLEANUP COMPLETE")
        print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

if __name__ == "__main__":
    # Check if live mode requested
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        dry_run = False
    
    cleanup = GancioDuplicateCleanup()
    cleanup.run_complete_cleanup(dry_run=dry_run)
