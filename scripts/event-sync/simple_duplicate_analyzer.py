#!/usr/bin/env python3
"""
Simple Duplicate Event Analyzer (Read-only, no auth required)
"""

import requests
import json
import hashlib
import re
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict

def normalize_title(title):
    """Normalize title for comparison"""
    if not title:
        return ""
    # Remove extra whitespace and convert to lowercase
    normalized = re.sub(r'\s+', ' ', title.strip().lower())
    # Remove special characters that might vary
    normalized = re.sub(r'[^\w\s]', '', normalized)
    # Remove common variations
    normalized = re.sub(r'\bwith\b|\band\b|\bfeat\b|\bfeaturing\b', ' ', normalized)
    return re.sub(r'\s+', ' ', normalized).strip()

def normalize_venue(venue_name):
    """Normalize venue name for comparison"""
    if not venue_name:
        return ""
    return venue_name.strip().lower()

def create_composite_key(event):
    """Create a composite key for event identification"""
    title = normalize_title(event.get('title', ''))
    venue = normalize_venue(event.get('place', {}).get('name', ''))
    # Use date (not timestamp) for matching events on same day
    start_time = event.get('start_datetime', 0)
    if isinstance(start_time, (int, float)):
        date = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
    else:
        date = str(start_time)[:10]
        
    return f"{title}|{venue}|{date}"

def titles_are_similar(title1, title2, threshold=0.8):
    """Check if two titles are similar"""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if norm1 == norm2:
        return True
        
    # Use sequence matcher for fuzzy matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity >= threshold

def analyze_duplicates():
    """Analyze duplicates in Gancio database"""
    print("📊 Fetching events from Gancio...")
    
    try:
        response = requests.get("http://localhost:13120/api/events")
        if response.status_code != 200:
            print(f"❌ Failed to fetch events: {response.status_code}")
            return
            
        events = response.json()
        print(f"📋 Found {len(events)} events total")
        
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return

    # Group events by composite key
    print("\n🔍 Grouping events by composite key (title + venue + date)...")
    grouped_events = defaultdict(list)
    
    for event in events:
        composite_key = create_composite_key(event)
        grouped_events[composite_key].append(event)
    
    # Find exact duplicates
    exact_duplicates = {key: events_list for key, events_list in grouped_events.items() if len(events_list) > 1}
    
    if not exact_duplicates:
        print("✨ No exact duplicate groups found!")
    else:
        print(f"\n🔍 Found {len(exact_duplicates)} groups with exact duplicates:")
        total_duplicates = 0
        
        for composite_key, duplicate_events in exact_duplicates.items():
            count = len(duplicate_events)
            total_duplicates += count - 1  # All but one are duplicates
            
            print(f"\n📌 Group: {count} events")
            print(f"   Key: {composite_key}")
            
            # Sort by ID (keep oldest)
            duplicate_events.sort(key=lambda x: x.get('id', 0))
            
            for i, event in enumerate(duplicate_events):
                status = "KEEP" if i == 0 else "REMOVE"
                print(f"   [{event.get('id', 'N/A')}] {status}: {event.get('title', 'No title')}")
        
        print(f"\n📊 Summary:")
        print(f"   Total duplicate groups: {len(exact_duplicates)}")
        print(f"   Total events to remove: {total_duplicates}")
        print(f"   Events to keep: {len(exact_duplicates)}")
    
    # Find potential fuzzy matches
    print(f"\n🔍 Checking for fuzzy duplicates (similar titles)...")
    fuzzy_matches = []
    
    processed = set()
    for i, event1 in enumerate(events):
        if event1['id'] in processed:
            continue
            
        matches = [event1]
        for j, event2 in enumerate(events[i+1:], i+1):
            if event2['id'] in processed:
                continue
                
            # Same date and venue check
            if (event1.get('start_datetime') == event2.get('start_datetime') and
                event1.get('place', {}).get('name') == event2.get('place', {}).get('name')):
                
                # Check title similarity
                if titles_are_similar(event1.get('title', ''), event2.get('title', ''), threshold=0.75):
                    matches.append(event2)
                    processed.add(event2['id'])
        
        if len(matches) > 1:
            fuzzy_matches.append(matches)
            for match in matches:
                processed.add(match['id'])
    
    if fuzzy_matches:
        print(f"\n🔍 Found {len(fuzzy_matches)} fuzzy duplicate groups:")
        for i, group in enumerate(fuzzy_matches):
            print(f"\n📌 Fuzzy Group {i+1}: {len(group)} events")
            for event in group:
                print(f"   [{event.get('id')}] {event.get('title', 'No title')}")
    else:
        print("✨ No fuzzy duplicates found!")

if __name__ == "__main__":
    analyze_duplicates()
