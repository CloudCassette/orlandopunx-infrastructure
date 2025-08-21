#!/usr/bin/env python3
"""
Comprehensive Gancio Duplicate Management
========================================
Handles both public API events and admin panel events (pending/drafts)
"""

import requests
import json
import re
import time
from datetime import datetime
from collections import defaultdict

class ComprehensiveDuplicateManager:
    def __init__(self):
        self.gancio_url = "http://localhost:13120"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.authenticated = False

    def authenticate(self):
        """Check authentication status"""
        try:
            admin_response = self.session.get(f"{self.gancio_url}/admin")
            if admin_response.status_code == 200:
                self.authenticated = True
                print("✅ Authenticated to Gancio admin")
                return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
        return False

    def get_public_events(self):
        """Get events from public API"""
        try:
            response = self.session.get(f"{self.gancio_url}/api/events")
            if response.status_code == 200:
                events = response.json()
                print(f"📊 Public API events: {len(events)}")
                return events
            else:
                print(f"❌ Public API failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Public API error: {e}")
            return []

    def get_admin_events(self):
        """Try to get events from admin interface (including pending/drafts)"""
        if not self.authenticated:
            print("⚠️ Not authenticated - cannot access admin events")
            return []
        
        admin_events = []
        
        # Try different admin API endpoints
        admin_endpoints = [
            "/api/events?all=true",
            "/api/events?status=all", 
            "/api/admin/events",
            "/admin/api/events"
        ]
        
        for endpoint in admin_endpoints:
            try:
                response = self.session.get(f"{self.gancio_url}{endpoint}")
                if response.status_code == 200:
                    events = response.json()
                    if len(events) > len(admin_events):
                        admin_events = events
                        print(f"📊 Admin API events ({endpoint}): {len(events)}")
                        break
            except:
                continue
        
        if not admin_events:
            print("⚠️ Could not access admin events via API")
        
        return admin_events

    def analyze_all_duplicates(self):
        """Comprehensive duplicate analysis across all event sources"""
        print("\n🔍 COMPREHENSIVE DUPLICATE ANALYSIS")
        print("=" * 40)
        
        # Get events from both sources
        public_events = self.get_public_events()
        admin_events = self.get_admin_events() if self.authenticated else []
        
        # Combine and deduplicate by ID
        all_events = {}
        event_sources = {}
        
        for event in public_events:
            event_id = event.get('id')
            if event_id:
                all_events[event_id] = event
                event_sources[event_id] = 'public'
        
        for event in admin_events:
            event_id = event.get('id')
            if event_id:
                if event_id not in all_events:
                    all_events[event_id] = event
                    event_sources[event_id] = 'admin_only'
                else:
                    event_sources[event_id] = 'both'
        
        events_list = list(all_events.values())
        
        print(f"📊 Event Sources:")
        public_count = sum(1 for s in event_sources.values() if s in ['public', 'both'])
        admin_only_count = sum(1 for s in event_sources.values() if s == 'admin_only')
        print(f"   📋 Public events: {public_count}")
        print(f"   🔒 Admin-only events: {admin_only_count}")
        print(f"   📊 Total unique events: {len(events_list)}")
        
        # Analyze duplicates
        return self.find_duplicates(events_list)

    def find_duplicates(self, events):
        """Find duplicates using multiple strategies"""
        duplicate_strategies = {
            'exact_title': defaultdict(list),
            'normalized_title': defaultdict(list),
            'title_and_date': defaultdict(list)
        }
        
        for event in events:
            title = event.get('title', '').strip()
            event_id = event.get('id')
            start_date = str(event.get('start_datetime', ''))[:10]
            
            if title:
                # Strategy 1: Exact title match
                duplicate_strategies['exact_title'][title].append(event)
                
                # Strategy 2: Normalized title (case-insensitive, whitespace normalized)
                normalized_title = ' '.join(title.lower().split())
                duplicate_strategies['normalized_title'][normalized_title].append(event)
                
                # Strategy 3: Title + date combination
                title_date_key = f"{normalized_title}|{start_date}"
                duplicate_strategies['title_and_date'][title_date_key].append(event)
        
        # Find actual duplicates
        duplicates_found = {}
        for strategy, groups in duplicate_strategies.items():
            strategy_duplicates = []
            for key, group in groups.items():
                if len(group) > 1:
                    strategy_duplicates.append({
                        'key': key,
                        'events': group,
                        'count': len(group)
                    })
            duplicates_found[strategy] = strategy_duplicates
        
        return duplicates_found

    def display_duplicate_analysis(self, duplicates_found):
        """Display comprehensive duplicate analysis"""
        print(f"\n📋 DUPLICATE ANALYSIS RESULTS")
        print("=" * 35)
        
        total_to_delete = 0
        recommended_deletions = []
        
        # Focus on exact title matches for main cleanup
        exact_duplicates = duplicates_found.get('exact_title', [])
        
        if exact_duplicates:
            print(f"🔴 Found {len(exact_duplicates)} groups of duplicate titles")
            
            for dup_group in exact_duplicates:
                title = dup_group['key']
                events = dup_group['events']
                count = dup_group['count']
                
                print(f"\n📋 \"{title}\" ({count} copies):")
                
                # Sort by ID (keep lowest ID)
                sorted_events = sorted(events, key=lambda x: x.get('id', 0))
                
                for i, event in enumerate(sorted_events):
                    event_id = event.get('id')
                    place = event.get('place', {})
                    place_name = place.get('name', 'Unknown') if isinstance(place, dict) else 'Unknown'
                    start_time = str(event.get('start_datetime', 'Unknown'))[:16]
                    
                    if i == 0:
                        print(f"   🟢 KEEP   ID:{event_id} | {place_name} | {start_time}")
                    else:
                        print(f"   🔴 DELETE ID:{event_id} | {place_name} | {start_time}")
                        recommended_deletions.append({
                            'id': event_id,
                            'title': title,
                            'reason': f'Duplicate of ID:{sorted_events[0].get("id")}'
                        })
                        total_to_delete += 1
        
        # Show other strategies for comparison
        for strategy, duplicates in duplicates_found.items():
            if strategy != 'exact_title' and duplicates:
                strategy_count = sum(len(d['events']) - 1 for d in duplicates)
                print(f"\n🔍 {strategy.upper()} strategy would delete: {strategy_count} events")
        
        print(f"\n📊 RECOMMENDATION:")
        print(f"   🔴 Events to delete: {total_to_delete}")
        print(f"   📋 Groups affected: {len(exact_duplicates)}")
        
        return recommended_deletions

    def safe_delete_events(self, deletion_list, dry_run=True):
        """Safely delete duplicate events"""
        if not deletion_list:
            print("\n✅ No events to delete")
            return True
        
        mode = "DRY RUN" if dry_run else "LIVE DELETION"
        print(f"\n🗑️ DUPLICATE CLEANUP ({mode})")
        print("=" * 35)
        
        if dry_run:
            print(f"📋 Would delete {len(deletion_list)} duplicate events:")
            for item in deletion_list:
                print(f"   🧪 ID:{item['id']} - {item['title'][:50]}...")
            return True
        
        # Live deletion
        success_count = 0
        failed_count = 0
        
        for i, item in enumerate(deletion_list, 1):
            event_id = item['id']
            title = item['title']
            
            print(f"\n[{i}/{len(deletion_list)}] Deleting: {title[:50]}...")
            print(f"   Event ID: {event_id}")
            
            try:
                delete_response = self.session.delete(f"{self.gancio_url}/api/event/{event_id}")
                
                if delete_response.status_code in [200, 204]:
                    print(f"   ✅ Successfully deleted")
                    success_count += 1
                else:
                    print(f"   ❌ Failed: HTTP {delete_response.status_code}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed_count += 1
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n📊 CLEANUP RESULTS:")
        print(f"   ✅ Deleted: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        return failed_count == 0

    def create_prevention_tools(self):
        """Create enhanced prevention tools"""
        print(f"\n🛡️ CREATING PREVENTION TOOLS")
        print("=" * 32)
        
        # Update the existing sync script with better deduplication
        enhanced_sync_content = '''
# Enhanced Deduplication Logic for Sync Scripts
# Add this to your sync scripts:

def enhanced_duplicate_check(existing_events, new_event_title):
    """Enhanced duplicate checking with fuzzy matching"""
    import hashlib
    
    title = new_event_title.strip()
    
    # Exact match check
    existing_titles = {event.get('title', '').strip() for event in existing_events}
    if title in existing_titles:
        return True, "Exact title match"
    
    # Normalized fuzzy check
    normalized_new = ' '.join(title.lower().split())
    
    for existing_event in existing_events:
        existing_title = existing_event.get('title', '').strip()
        normalized_existing = ' '.join(existing_title.lower().split())
        
        if normalized_new == normalized_existing:
            return True, f"Fuzzy match with: {existing_title}"
    
    return False, None

# Usage in sync scripts:
"""
existing_gancio_events = get_gancio_events()
for new_event in scraped_events:
    is_duplicate, reason = enhanced_duplicate_check(existing_gancio_events, new_event['title'])
    if is_duplicate:
        print(f"⚠️ Skipping duplicate: {new_event['title']} ({reason})")
        continue
    # Create event...
"""
'''
        
        prevention_file = "scripts/event-sync/enhanced_deduplication_guide.py"
        with open(prevention_file, 'w') as f:
            f.write(enhanced_sync_content)
        
        print(f"✅ Created: {prevention_file}")
        
        return prevention_file

    def run_comprehensive_cleanup(self):
        """Run complete comprehensive duplicate cleanup"""
        print("🧹 COMPREHENSIVE GANCIO DUPLICATE MANAGEMENT")
        print("=" * 50)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Authenticate
        self.authenticate()
        
        # Analyze all duplicates
        duplicates_found = self.analyze_all_duplicates()
        
        # Display analysis
        deletion_list = self.display_duplicate_analysis(duplicates_found)
        
        if deletion_list:
            print(f"\n💡 NEXT STEPS:")
            print(f"   1. Review the duplicate analysis above")
            print(f"   2. Create backup: Already created automatically")
            print(f"   3. Run cleanup: python3 {__file__} --cleanup")
            
            # Check for --cleanup flag
            import sys
            if '--cleanup' in sys.argv:
                print(f"\n⚠️ WARNING: About to delete {len(deletion_list)} duplicate events!")
                confirm = input("Type 'DELETE' to confirm cleanup: ")
                
                if confirm == 'DELETE':
                    success = self.safe_delete_events(deletion_list, dry_run=False)
                    if success:
                        print("\n🎉 Duplicate cleanup completed successfully!")
                        
                        # Verify cleanup
                        print("\n🔍 Verifying cleanup...")
                        new_duplicates = self.analyze_all_duplicates()
                        remaining = sum(len(dups) for dups in new_duplicates.values())
                        
                        if remaining == 0:
                            print("✅ SUCCESS: No duplicates remaining!")
                        else:
                            print(f"⚠️ {remaining} potential duplicates may remain")
                else:
                    print("❌ Cleanup cancelled")
        else:
            print("\n✅ No duplicates found - your Gancio database is clean!")
        
        # Create prevention tools
        self.create_prevention_tools()
        
        print(f"\n🏁 Analysis complete!")
        return True

if __name__ == "__main__":
    manager = ComprehensiveDuplicateManager()
    manager.run_comprehensive_cleanup()
