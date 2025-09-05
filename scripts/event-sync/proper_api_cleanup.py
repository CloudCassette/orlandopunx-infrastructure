#!/usr/bin/env python3
"""
Proper Gancio API Duplicate Cleanup
===================================
Uses the documented Gancio API with JWT authentication to find and clean up duplicates
"""

import requests
import os
import json
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

class GancioJWTCleanup:
    """Clean up duplicates using proper JWT authentication"""
    
    def __init__(self, base_url: str = "http://localhost:13120"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        
        # Set proper headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        })
    
    def authenticate(self) -> bool:
        """Authenticate using JWT token method from docs"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")
        
        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False
            
        print(f"🔑 Authenticating with JWT as {email}...")
        
        try:
            # Use the documented JWT login endpoint
            auth_data = {
                "email": email,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/login/token",
                json=auth_data  # Use JSON as shown in docs
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                
                if self.access_token:
                    # Set the authorization header for future requests
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}'
                    })
                    print("✅ JWT authentication successful!")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            else:
                print(f"❌ JWT authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_all_events_paginated(self) -> List[Dict]:
        """Get ALL events using proper pagination from the API docs"""
        all_events = []
        page = 1
        max_per_page = 100  # Try larger batches
        
        print("📊 Fetching all events with proper pagination...")
        
        while True:
            try:
                # Use documented API parameters
                params = {
                    'page': page,
                    'max': max_per_page,
                    'start': 0,  # Get events from beginning of time
                    'older': True,  # Include older events
                    'show_multidate': True,
                    'show_recurrent': True
                }
                
                response = self.session.get(
                    f"{self.base_url}/api/events",
                    params=params
                )
                
                if response.status_code == 200:
                    events = response.json()
                    
                    if not events or len(events) == 0:
                        print(f"📋 Page {page}: No more events")
                        break
                        
                    print(f"📋 Page {page}: Found {len(events)} events")
                    all_events.extend(events)
                    
                    # If we got less than max_per_page, we're done
                    if len(events) < max_per_page:
                        print(f"📋 Last page reached (got {len(events)} < {max_per_page})")
                        break
                        
                    page += 1
                    
                    # Safety break to avoid infinite loops
                    if page > 100:
                        print("⚠️ Safety break: stopping at page 100")
                        break
                        
                else:
                    print(f"❌ API error on page {page}: {response.status_code}")
                    print(f"Response: {response.text}")
                    break
                    
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
        
        print(f"✅ Total events fetched: {len(all_events)}")
        return all_events
    
    def get_pending_events(self) -> List[Dict]:
        """Try to get pending/unapproved events"""
        print("🔍 Attempting to fetch pending events...")
        
        # The API docs don't show how to get pending events specifically
        # But let's try some approaches
        pending_events = []
        
        # Try different approaches to get unapproved events
        endpoints_to_try = [
            ("/api/events", {"approved": "false"}),
            ("/api/events", {"status": "pending"}),
            ("/api/events", {"status": "draft"}),
            ("/api/events", {"is_active": "false"}),
        ]
        
        for endpoint, extra_params in endpoints_to_try:
            try:
                params = {
                    'max': 1000,
                    'start': 0,
                    'older': True,
                    **extra_params
                }
                
                response = self.session.get(f"{self.base_url}{endpoint}", params=params)
                
                if response.status_code == 200:
                    events = response.json()
                    print(f"  📋 {endpoint} with {extra_params}: {len(events)} events")
                    
                    # Add to pending events if not already there
                    existing_ids = {e.get('id') for e in pending_events}
                    new_events = [e for e in events if e.get('id') not in existing_ids]
                    pending_events.extend(new_events)
                    
                else:
                    print(f"  ❌ {endpoint}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {endpoint}: {e}")
        
        print(f"📊 Total unique pending events found: {len(pending_events)}")
        return pending_events
    
    def create_event_signature(self, event: Dict) -> str:
        """Create a signature for event deduplication"""
        title = self._normalize_text(event.get("title", ""))
        place = event.get("place", {})
        venue = self._normalize_text(place.get("name", "") if place else "")
        
        # Use date only for grouping  
        start_time = event.get("start_datetime", 0)
        if isinstance(start_time, (int, float)):
            date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")
        else:
            date = str(start_time)[:10]
            
        return f"{title}|{venue}|{date}"
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        import re
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        normalized = re.sub(r"[^\w\s]", "", normalized)
        return normalized
    
    def find_duplicate_groups(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Find groups of duplicate events"""
        signature_groups = defaultdict(list)
        
        for event in events:
            signature = self.create_event_signature(event)
            signature_groups[signature].append(event)
        
        # Filter to only groups with duplicates
        duplicates = {
            sig: events_list
            for sig, events_list in signature_groups.items()
            if len(events_list) > 1
        }
        
        return duplicates
    
    def analyze_all_events(self):
        """Analyze all events for duplicates"""
        print("🔍 ANALYZING ALL EVENTS FOR DUPLICATES")
        print("=" * 50)
        
        all_events = self.get_all_events_paginated()
        
        if not all_events:
            print("⚠️ No events found")
            return
            
        duplicate_groups = self.find_duplicate_groups(all_events)
        
        print(f"\n📊 DUPLICATE ANALYSIS RESULTS:")
        print(f"   Total events: {len(all_events)}")
        print(f"   Duplicate groups: {len(duplicate_groups)}")
        
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print(f"   Events to remove: {total_duplicates}")
        
        if duplicate_groups:
            print(f"\n🔍 DUPLICATE GROUPS PREVIEW:")
            for i, (signature, events_group) in enumerate(list(duplicate_groups.items())[:5]):
                print(f"\n{i+1}. Group: {signature}")
                for j, event in enumerate(events_group):
                    marker = "✅ KEEP" if j == 0 else "❌ REMOVE"
                    print(f"   {marker}: [{event.get('id')}] {event.get('title', 'No title')[:50]}...")
            
            if len(duplicate_groups) > 5:
                print(f"\n... and {len(duplicate_groups) - 5} more groups")
    
    def analyze_pending_events(self):
        """Analyze pending events specifically"""
        print("🔍 ANALYZING PENDING EVENTS FOR DUPLICATES")  
        print("=" * 50)
        
        pending_events = self.get_pending_events()
        
        if not pending_events:
            print("⚠️ No pending events found")
            return
            
        duplicate_groups = self.find_duplicate_groups(pending_events)
        
        print(f"\n📊 PENDING DUPLICATE ANALYSIS:")
        print(f"   Total pending events: {len(pending_events)}")
        print(f"   Duplicate groups: {len(duplicate_groups)}")
        
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print(f"   Events to remove: {total_duplicates}")
        
        return duplicate_groups
    
    def delete_event(self, event_id: int) -> bool:
        """Delete an event using the API"""
        try:
            response = self.session.delete(f"{self.base_url}/api/events/{event_id}")
            return response.status_code in [200, 204, 404]
        except:
            return False
    
    def cleanup_duplicates(self, groups: Dict, dry_run: bool = True) -> bool:
        """Clean up duplicate events"""
        if not groups:
            print("✨ No duplicates to clean up!")
            return True
            
        total_to_remove = sum(len(group) - 1 for group in groups.values())
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would remove {total_to_remove} duplicate events")
            return True
            
        print(f"\n🗑️ CLEANUP: Removing {total_to_remove} duplicate events...")
        print("⚠️ THIS WILL PERMANENTLY DELETE EVENTS!")
        
        confirmation = input("\nType 'DELETE' to confirm: ")
        if confirmation != "DELETE":
            print("❌ Cleanup cancelled")
            return False
            
        removed_count = 0
        error_count = 0
        
        for signature, events_group in groups.items():
            # Sort by ID to keep the oldest
            events_sorted = sorted(events_group, key=lambda x: x.get("id", 999999))
            keep_event = events_sorted[0]
            remove_events = events_sorted[1:]
            
            print(f"\n📌 Processing: {signature}")
            print(f"   ✅ Keeping: [{keep_event.get('id')}] {keep_event.get('title', 'No title')[:50]}...")
            
            for event in remove_events:
                event_id = event.get('id')
                if self.delete_event(event_id):
                    print(f"   ✅ Removed: [{event_id}]")
                    removed_count += 1
                else:
                    print(f"   ❌ Failed to remove: [{event_id}]")
                    error_count += 1
        
        print(f"\n📊 Cleanup Summary:")
        print(f"   ✅ Removed: {removed_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return error_count == 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up duplicates using proper Gancio API")
    parser.add_argument("--analyze-all", action="store_true", help="Analyze all events")
    parser.add_argument("--analyze-pending", action="store_true", help="Analyze pending events")
    parser.add_argument("--cleanup-pending", action="store_true", help="Clean up pending duplicates")
    parser.add_argument("--cleanup-all", action="store_true", help="Clean up all duplicates")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run (default)")
    parser.add_argument("--force", action="store_true", help="Actually delete (not dry run)")
    
    args = parser.parse_args()
    
    if not any([args.analyze_all, args.analyze_pending, args.cleanup_pending, args.cleanup_all]):
        parser.print_help()
        return 1
    
    print("🧹 Proper Gancio API Duplicate Cleanup")
    print("======================================")
    
    cleaner = GancioJWTCleanup()
    
    if not cleaner.authenticate():
        return 1
    
    try:
        if args.analyze_all:
            cleaner.analyze_all_events()
            
        elif args.analyze_pending:
            cleaner.analyze_pending_events()
            
        elif args.cleanup_pending:
            groups = cleaner.analyze_pending_events()
            if groups:
                cleaner.cleanup_duplicates(groups, dry_run=not args.force)
                
        elif args.cleanup_all:
            all_events = cleaner.get_all_events_paginated()
            groups = cleaner.find_duplicate_groups(all_events)
            if groups:
                cleaner.cleanup_duplicates(groups, dry_run=not args.force)
                
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
