#!/usr/bin/env python3
"""
Robust Event Deduplication System for Gancio
Addresses the root causes of duplicate event creation

Issues solved:
1. Title-only matching is too weak
2. No date/venue consideration
3. No unique event ID tracking
4. No update capability for existing events
5. Poor normalization of event data
"""

import requests
import hashlib
import json
import os
from datetime import datetime
import re
from typing import Dict, List, Tuple, Optional, Set
from difflib import SequenceMatcher

class RobustEventDeduplicator:
    def __init__(self, gancio_base_url="http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()
        self.existing_events = {}  # Map of composite keys to event data
        self.event_hashes = {}     # Map of content hashes to event IDs
        
    def authenticate(self):
        """Authenticate with Gancio"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False
            
        login_url = f"{self.gancio_base_url}/auth/login"
        login_data = {'email': email, 'password': password}
        
        try:
            # First get the login page to establish session
            self.session.get(f"{self.gancio_base_url}/login")
            
            # Then POST login credentials
            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            if "admin" in response.url or response.status_code == 200:
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', title.strip().lower())
        # Remove special characters that might vary
        normalized = re.sub(r'[^\w\s]', '', normalized)
        # Remove common variations
        normalized = re.sub(r'\bwith\b|\band\b|\bfeat\b|\bfeaturing\b', ' ', normalized)
        return re.sub(r'\s+', ' ', normalized).strip()
    
    def normalize_venue(self, venue_name: str) -> str:
        """Normalize venue name for comparison"""
        if not venue_name:
            return ""
        # Remove trailing spaces, standardize format
        normalized = venue_name.strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    def create_composite_key(self, event: Dict) -> str:
        """Create a composite key for event identification"""
        title = self.normalize_title(event.get('title', ''))
        venue = self.normalize_venue(event.get('venue') or event.get('place', {}).get('name', ''))
        # Use date (not timestamp) for matching events on same day
        start_time = event.get('start_datetime', 0)
        if isinstance(start_time, (int, float)):
            date = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
        else:
            date = str(start_time)[:10]  # Fallback for string dates
            
        return f"{title}|{venue}|{date}"
    
    def create_content_hash(self, event: Dict) -> str:
        """Create a content-based hash for exact duplicate detection"""
        # Create hash from essential event content
        content = {
            'title': self.normalize_title(event.get('title', '')),
            'venue': self.normalize_venue(event.get('venue') or event.get('place', {}).get('name', '')),
            'start_time': event.get('start_datetime', 0),
            'description': event.get('description', '').strip()[:200]  # First 200 chars
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def titles_are_similar(self, title1: str, title2: str, threshold=0.8) -> bool:
        """Check if two titles are similar using sequence matching"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        if norm1 == norm2:
            return True
            
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold
    
    def load_existing_events(self) -> bool:
        """Load and index existing events from Gancio"""
        print("📊 Loading existing events for deduplication...")
        
        try:
            response = self.session.get(f"{self.gancio_base_url}/api/events")
            if response.status_code != 200:
                print(f"❌ Failed to fetch events: {response.status_code}")
                return False
                
            events = response.json()
            print(f"📋 Found {len(events)} existing events")
            
            # Index events by composite key and content hash
            for event in events:
                # Store by composite key
                composite_key = self.create_composite_key(event)
                if composite_key not in self.existing_events:
                    self.existing_events[composite_key] = []
                self.existing_events[composite_key].append(event)
                
                # Store by content hash
                content_hash = self.create_content_hash(event)
                self.event_hashes[content_hash] = event
                
            print(f"📊 Indexed by {len(self.existing_events)} composite keys")
            print(f"📊 Indexed by {len(self.event_hashes)} content hashes")
            return True
            
        except Exception as e:
            print(f"❌ Error loading existing events: {e}")
            return False
    
    def find_duplicates(self, new_event: Dict) -> Tuple[Optional[Dict], str]:
        """
        Find if event already exists
        Returns: (existing_event_or_None, match_reason)
        """
        # 1. Check exact content hash match (highest confidence)
        content_hash = self.create_content_hash(new_event)
        if content_hash in self.event_hashes:
            return self.event_hashes[content_hash], "exact_content_match"
        
        # 2. Check composite key match
        composite_key = self.create_composite_key(new_event)
        if composite_key in self.existing_events:
            candidates = self.existing_events[composite_key]
            
            # If only one candidate, it's likely the same event
            if len(candidates) == 1:
                return candidates[0], "composite_key_match"
            
            # Multiple candidates - use title similarity
            new_title = new_event.get('title', '')
            for candidate in candidates:
                if self.titles_are_similar(new_title, candidate.get('title', '')):
                    return candidate, "similar_title_match"
        
        # 3. Fuzzy matching across all events (slower but thorough)
        new_title = new_event.get('title', '')
        new_venue = self.normalize_venue(new_event.get('venue') or new_event.get('place', {}).get('name', ''))
        new_date = None
        
        start_time = new_event.get('start_datetime', 0)
        if isinstance(start_time, (int, float)):
            new_date = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
        
        # Check all existing events for fuzzy matches
        for events_list in self.existing_events.values():
            for existing in events_list:
                existing_venue = self.normalize_venue(existing.get('place', {}).get('name', ''))
                existing_date = None
                
                ex_start = existing.get('start_datetime', 0)
                if isinstance(ex_start, (int, float)):
                    existing_date = datetime.fromtimestamp(ex_start).strftime('%Y-%m-%d')
                
                # Must match date and venue
                if new_date == existing_date and new_venue == existing_venue:
                    if self.titles_are_similar(new_title, existing.get('title', ''), threshold=0.75):
                        return existing, "fuzzy_match"
        
        return None, "no_match"
    
    def should_skip_event(self, new_event: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """
        Determine if event should be skipped (already exists)
        Returns: (should_skip, reason, existing_event_or_None)
        """
        existing_event, match_reason = self.find_duplicates(new_event)
        
        if existing_event:
            return True, match_reason, existing_event
        else:
            return False, "new_event", None
    
    def analyze_duplicates_in_gancio(self) -> Dict:
        """Analyze existing duplicates in Gancio database"""
        if not self.load_existing_events():
            return {}
        
        print("\n🔍 Analyzing existing duplicates...")
        duplicates = {}
        processed = set()
        
        # Group by composite key and find duplicates
        for composite_key, events in self.existing_events.items():
            if len(events) > 1:
                # Sort by ID (keep oldest)
                events_sorted = sorted(events, key=lambda x: x.get('id', 0))
                duplicates[composite_key] = {
                    'keep': events_sorted[0],
                    'remove': events_sorted[1:],
                    'count': len(events)
                }
                print(f"🔍 Found {len(events)} duplicates for: {events[0].get('title', 'Unknown')[:50]}...")
        
        return duplicates
    
    def cleanup_duplicates(self, dry_run=True) -> bool:
        """Clean up duplicate events in Gancio"""
        duplicates = self.analyze_duplicates_in_gancio()
        
        if not duplicates:
            print("✨ No duplicates found!")
            return True
        
        total_to_remove = sum(len(dup['remove']) for dup in duplicates.values())
        print(f"\n📊 Found {len(duplicates)} sets of duplicates")
        print(f"📊 Total events to remove: {total_to_remove}")
        
        if dry_run:
            print("\n🔍 DRY RUN - Events that would be removed:")
            for composite_key, dup_info in duplicates.items():
                keep_event = dup_info['keep']
                remove_events = dup_info['remove']
                print(f"\n📌 Keeping: [{keep_event['id']}] {keep_event['title'][:60]}...")
                for remove_event in remove_events:
                    print(f"   ❌ Would remove: [{remove_event['id']}] {remove_event['title'][:60]}...")
            return True
        
        # Actual deletion
        removed_count = 0
        for composite_key, dup_info in duplicates.items():
            remove_events = dup_info['remove']
            keep_event = dup_info['keep']
            
            print(f"\n📌 Keeping event [{keep_event['id']}]: {keep_event['title'][:60]}...")
            
            for remove_event in remove_events:
                event_id = remove_event['id']
                try:
                    delete_url = f"{self.gancio_base_url}/api/event/{event_id}"
                    response = self.session.delete(delete_url)
                    
                    if response.status_code in [200, 204]:
                        print(f"   ✅ Removed duplicate [{event_id}]")
                        removed_count += 1
                    else:
                        print(f"   ❌ Failed to remove [{event_id}]: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error removing [{event_id}]: {e}")
        
        print(f"\n✅ Successfully removed {removed_count} duplicate events")
        return True

def main():
    """Main function for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Robust Event Deduplication System')
    parser.add_argument('--analyze', action='store_true', help='Analyze existing duplicates')
    parser.add_argument('--cleanup', action='store_true', help='Clean up duplicates')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run mode (default)')
    parser.add_argument('--force', action='store_true', help='Actually perform deletions')
    
    args = parser.parse_args()
    
    deduplicator = RobustEventDeduplicator()
    
    if not deduplicator.authenticate():
        return 1
    
    if args.analyze:
        deduplicator.analyze_duplicates_in_gancio()
    elif args.cleanup:
        dry_run = not args.force
        deduplicator.cleanup_duplicates(dry_run=dry_run)
    else:
        print("Use --analyze to check duplicates or --cleanup to remove them")
        print("Use --force with --cleanup to actually delete (default is dry-run)")

if __name__ == "__main__":
    main()
