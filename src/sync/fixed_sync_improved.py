#!/usr/bin/env python3
"""
Fixed Event Sync System - With Real Event Fetching & Robust Duplicate Detection
===============================================================================

Key improvements:
1. Integrates real event scrapers (Will's Pub, etc.)
2. Robust duplicate detection using direct DB access
3. Checks BOTH published AND unconfirmed events
4. Normalizes titles and compares with venue names
5. Handles slug variants with numeric suffixes
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup


class ImprovedEventSync:
    """Improved sync system with real fetching and robust deduplication"""

    def __init__(self):
        self.gancio_base_url = os.environ.get(
            "GANCIO_BASE_URL", "http://localhost:13120"
        )
        self.gancio_email = os.environ.get("GANCIO_EMAIL", "admin")
        self.gancio_password = os.environ.get("GANCIO_PASSWORD", "")
        self.session = requests.Session()
        self.existing_events = {}
        self.existing_by_title_venue = {}
        self.db_path = "/var/lib/gancio/gancio.sqlite"

    def load_all_existing_events(self):
        """Load ALL events with enhanced duplicate detection indexes"""
        print("📊 Loading existing events for duplicate checking...")

        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get ALL events with venue information
                cursor.execute("""
                    SELECT 
                        e.id, 
                        e.title, 
                        e.slug, 
                        e.start_datetime, 
                        e.placeId, 
                        e.is_visible,
                        p.name as place_name
                    FROM events e
                    LEFT JOIN places p ON e.placeId = p.id
                    ORDER BY e.id DESC
                """)

                db_events = cursor.fetchall()
                conn.close()

                print(f"   📁 Found {len(db_events)} total events in database")

                for event_id, title, slug, start_dt, place_id, is_visible, place_name in db_events:
                    # Store by slug
                    self.existing_events[slug] = {
                        "id": event_id,
                        "title": title,
                        "slug": slug,
                        "is_visible": is_visible,
                        "place_name": place_name or "",
                        "start_datetime": start_dt
                    }

                    # Store by base slug (without number suffix)
                    base_slug = re.sub(r'-\d+$', '', slug) if slug else ""
                    if base_slug and base_slug != slug:
                        if base_slug not in self.existing_events:
                            self.existing_events[base_slug] = []
                        if isinstance(self.existing_events[base_slug], list):
                            self.existing_events[base_slug].append({
                                "id": event_id,
                                "title": title,
                                "slug": slug,
                                "is_visible": is_visible,
                                "place_name": place_name or "",
                                "start_datetime": start_dt
                            })

                    # Create normalized title+venue key for robust matching
                    normalized_title = self.normalize_text(title)
                    normalized_venue = self.normalize_text(place_name or "")
                    title_venue_key = f"{normalized_title}|{normalized_venue}"
                    
                    if title_venue_key not in self.existing_by_title_venue:
                        self.existing_by_title_venue[title_venue_key] = []
                    self.existing_by_title_venue[title_venue_key].append({
                        "id": event_id,
                        "title": title,
                        "slug": slug,
                        "is_visible": is_visible,
                        "start_datetime": start_dt
                    })

                published_count = sum(1 for e in db_events if e[5] == 1)
                unconfirmed_count = len(db_events) - published_count
                print(f"   ✅ Loaded {published_count} published, {unconfirmed_count} unconfirmed events")
                return True

            except Exception as e:
                print(f"   ⚠️ Could not read database directly: {e}")
                return False

        print("   ⚠️ Database not found, duplicate detection will be limited")
        return False

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        # Convert to lowercase, remove special chars, collapse whitespace
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def create_event_slug(self, title: str, venue: str = "") -> str:
        """Create a slug from event title and venue"""
        text = f"{title} {venue}".lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', text)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:100]

    def is_duplicate_event(self, event: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Enhanced duplicate detection checking multiple criteria
        """
        title = event.get("title", "")
        venue = event.get("venue", "")
        event_date = event.get("date", "")
        
        # Normalize for comparison
        norm_title = self.normalize_text(title)
        norm_venue = self.normalize_text(venue)
        title_venue_key = f"{norm_title}|{norm_venue}"

        # Check 1: Exact title+venue match
        if title_venue_key in self.existing_by_title_venue:
            existing_list = self.existing_by_title_venue[title_venue_key]
            # Check if any have same date (within same day)
            for existing in existing_list:
                if event_date and existing.get("start_datetime"):
                    try:
                        existing_date = existing["start_datetime"].split("T")[0]
                        if existing_date == event_date:
                            print(f"   🔍 Found duplicate by title+venue+date: {title}")
                            return True, existing
                    except:
                        pass
            # Even without date match, if title+venue match exactly, likely duplicate
            if existing_list:
                print(f"   🔍 Found duplicate by title+venue: {title}")
                return True, existing_list[0]

        # Check 2: Slug-based matching
        potential_slug = self.create_event_slug(title, venue)
        
        # Direct slug match
        if potential_slug in self.existing_events:
            existing = self.existing_events[potential_slug]
            if isinstance(existing, dict):
                print(f"   🔍 Found duplicate by slug: {potential_slug}")
                return True, existing

        # Base slug match (ignoring numeric suffixes)
        base_slug = re.sub(r'-\d+$', '', potential_slug)
        if base_slug in self.existing_events:
            existing = self.existing_events[base_slug]
            if isinstance(existing, list) and len(existing) > 0:
                print(f"   🔍 Found variants with base slug: {base_slug}")
                return True, existing[0]
            elif isinstance(existing, dict):
                print(f"   🔍 Found duplicate by base slug: {base_slug}")
                return True, existing

        # Check 3: Fuzzy title matching at same venue
        for slug, existing in self.existing_events.items():
            if isinstance(existing, dict):
                existing_title = existing.get("title", "")
                existing_venue = existing.get("place_name", "")
                
                # Very similar titles at the same venue
                if norm_venue and norm_venue == self.normalize_text(existing_venue):
                    if norm_title in self.normalize_text(existing_title) or \
                       self.normalize_text(existing_title) in norm_title:
                        print(f"   🔍 Found similar event at same venue: {existing_title}")
                        return True, existing

        return False, None

    def fetch_willspub_events(self) -> List[Dict]:
        """Fetch events from Will's Pub"""
        print("🎸 Fetching Will's Pub events...")
        events = []
        
        try:
            url = "https://willspub.org/"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find event containers
            event_blocks = soup.find_all('div', class_='tribe-events-calendar-list__event')
            
            for block in event_blocks[:20]:  # Limit to 20 events
                try:
                    # Get title
                    title_elem = block.find('h3', class_='tribe-events-calendar-list__event-title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Get date
                    date_elem = block.find('time', class_='tribe-events-calendar-list__event-datetime')
                    event_date = datetime.now().strftime("%Y-%m-%d")
                    event_time = "20:00"
                    
                    if date_elem and date_elem.get('datetime'):
                        try:
                            dt = datetime.fromisoformat(date_elem['datetime'].replace('Z', '+00:00'))
                            event_date = dt.strftime("%Y-%m-%d")
                            event_time = dt.strftime("%H:%M")
                        except:
                            pass
                    
                    # Get description
                    desc_elem = block.find('div', class_='tribe-events-calendar-list__event-description')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    events.append({
                        "title": title,
                        "venue": "Will's Pub",
                        "date": event_date,
                        "time": event_time,
                        "description": description[:500],  # Limit description length
                        "tags": ["punk", "live-music"],
                        "place_id": 1  # Will's Pub venue ID in Gancio
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Error parsing event: {e}")
                    continue
            
            print(f"   ✅ Found {len(events)} events from Will's Pub")
            
        except Exception as e:
            print(f"   ❌ Error fetching Will's Pub events: {e}")
        
        return events

    def submit_event(self, event: Dict) -> bool:
        """Submit an event to Gancio only if it's not a duplicate"""
        
        # Check for duplicates first
        is_dup, existing = self.is_duplicate_event(event)
        
        if is_dup:
            print(f"   ⏭️  Skipping duplicate: {event.get('title', 'Unknown')}")
            if existing:
                status = "published" if existing.get('is_visible') == 1 else "unconfirmed"
                print(f"      Already exists as {status} event ID: {existing.get('id')}")
            return False

        # DRY RUN check
        if os.environ.get("DRY_RUN", "").lower() in {"1", "true", "yes"}:
            print(f"   🧪 DRY RUN - Would submit: {event.get('title', 'Unknown')}")
            return True

        # Event is unique, prepare for submission
        print(f"   📤 Submitting new event: {event.get('title', 'Unknown')}")
        
        try:
            # Convert date/time to datetime object
            event_datetime = datetime.strptime(
                f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M"
            )
            end_datetime = event_datetime + timedelta(hours=3)
            
            gancio_event = {
                "title": event.get("title"),
                "description": event.get("description", ""),
                "start_datetime": event_datetime.isoformat(),
                "end_datetime": end_datetime.isoformat(),
                "place_id": event.get("place_id", 1),
                "tags": event.get("tags", []),
            }
            
            response = self.session.post(
                f"{self.gancio_base_url}/api/event",
                json=gancio_event
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Event created successfully")
                # Add to our cache to prevent re-submission
                slug = self.create_event_slug(event.get("title"), event.get("venue"))
                self.existing_events[slug] = {
                    "id": "new",
                    "title": event.get("title"),
                    "slug": slug,
                }
                return True
            else:
                print(f"   ❌ Creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error submitting event: {e}")
            return False

    def run_sync(self):
        """Run the sync process with real event fetching"""
        
        print("\n🚀 Starting Improved Event Sync")
        print("=" * 60)
        
        # Load ALL existing events (including unconfirmed)
        self.load_all_existing_events()
        
        # Fetch events from various sources
        all_events = []
        
        # Fetch from Will's Pub
        willspub_events = self.fetch_willspub_events()
        all_events.extend(willspub_events)
        
        print(f"\n📋 Total events to process: {len(all_events)}")
        
        # Process events
        submitted = 0
        skipped = 0
        failed = 0
        
        for event in all_events:
            try:
                if self.submit_event(event):
                    submitted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"   ❌ Error processing event: {e}")
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Sync Summary:")
        print(f"   ✅ Submitted: {submitted} new events")
        print(f"   ⏭️  Skipped: {skipped} duplicates")
        print(f"   ❌ Failed: {failed} events")
        print(f"   📚 Total existing: {len(self.existing_events)} events in database")
        
        return submitted > 0 or skipped > 0


def main():
    """Main entry point"""
    
    # Check for DRY_RUN mode
    if os.environ.get("DRY_RUN", "").lower() in {"1", "true", "yes"}:
        print("🧪 DRY RUN MODE - No events will be submitted")
    
    sync = ImprovedEventSync()
    success = sync.run_sync()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
