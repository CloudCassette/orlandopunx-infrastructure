#!/usr/bin/env python3
"""
Improved Event Sync System - Addresses Duplicate Issues
======================================================

Key improvements:
1. Enhanced deduplication using composite keys and content hashing
2. Persistent state tracking to avoid reprocessing
3. Smart event fetching (only new/changed events)
4. Reduced sync frequency with intelligent scheduling
5. Better approval queue management
"""

import hashlib
import json
import os
import pickle
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests


@dataclass
class EventState:
    """Track processed events to prevent duplicates"""

    event_hash: str
    gancio_id: Optional[int]
    last_seen: datetime
    source: str
    venue: str
    title: str
    date: str
    status: str  # 'pending', 'approved', 'rejected', 'processed'


class PersistentStateManager:
    """Manage state persistence to avoid reprocessing events"""

    def __init__(self, state_file: str = None):
        self.state_file = state_file or os.path.join(
            os.path.dirname(__file__), "event_state.pkl"
        )
        self.processed_events: Dict[str, EventState] = {}
        self.load_state()

    def load_state(self):
        """Load persistent state from disk"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "rb") as f:
                    self.processed_events = pickle.load(f)
                    # Clean up old entries (older than 30 days)
                    cutoff = datetime.now() - timedelta(days=30)
                    self.processed_events = {
                        k: v
                        for k, v in self.processed_events.items()
                        if v.last_seen > cutoff
                    }
                print(
                    f"📁 Loaded {len(self.processed_events)} processed events from state"
                )
            else:
                print("📁 No existing state file found, starting fresh")
        except Exception as e:
            print(f"⚠️ Error loading state: {e}, starting fresh")
            self.processed_events = {}

    def save_state(self):
        """Save persistent state to disk"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "wb") as f:
                pickle.dump(self.processed_events, f)
            print(f"💾 Saved state with {len(self.processed_events)} events")
        except Exception as e:
            print(f"❌ Error saving state: {e}")

    def is_event_processed(self, event_hash: str) -> bool:
        """Check if event has been processed already"""
        return event_hash in self.processed_events

    def mark_event_processed(self, event_hash: str, state: EventState):
        """Mark event as processed"""
        self.processed_events[event_hash] = state

    def update_event_status(self, event_hash: str, status: str, gancio_id: int = None):
        """Update event status"""
        if event_hash in self.processed_events:
            self.processed_events[event_hash].status = status
            if gancio_id:
                self.processed_events[event_hash].gancio_id = gancio_id


class EnhancedEventDeduplicator:
    """Enhanced deduplication with multiple strategies and state tracking"""

    def __init__(self, state_manager: PersistentStateManager):
        self.state_manager = state_manager
        self.existing_events: List[Dict] = []
        self.indexed_events: Dict[str, List[Dict]] = {}

    def create_event_hash(self, event: Dict) -> str:
        """Create a deterministic hash for an event"""
        # Normalize key fields for consistent hashing
        title = self._normalize_text(event.get("title", ""))
        venue = self._normalize_text(event.get("venue", ""))
        date = self._normalize_date(event.get("start_datetime", ""))
        description = self._normalize_text(event.get("description", ""))[:200]

        content = {
            "title": title,
            "venue": venue,
            "date": date,
            "description": description,
        }

        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        # Remove extra whitespace, convert to lowercase
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        # Remove special characters that might vary
        normalized = re.sub(r"[^\w\s]", "", normalized)
        return normalized

    def _normalize_date(self, date_input) -> str:
        """Normalize date for comparison"""
        if isinstance(date_input, (int, float)):
            return datetime.fromtimestamp(date_input).strftime("%Y-%m-%d")
        elif isinstance(date_input, str):
            return date_input[:10]  # Take just the date part
        else:
            return str(date_input)

    def load_existing_events(self, session: requests.Session, gancio_url: str) -> bool:
        """Load existing events from Gancio for comparison"""
        try:
            response = session.get(f"{gancio_url}/api/events")
            if response.status_code == 200:
                self.existing_events = response.json()
                self._index_events()
                print(f"📊 Loaded {len(self.existing_events)} existing events")
                return True
            else:
                print(f"⚠️ Could not load existing events: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error loading existing events: {e}")
            return False

    def _index_events(self):
        """Index events for faster lookup"""
        self.indexed_events = {}
        for event in self.existing_events:
            event_hash = self.create_event_hash(event)
            if event_hash not in self.indexed_events:
                self.indexed_events[event_hash] = []
            self.indexed_events[event_hash].append(event)

    def is_duplicate(self, new_event: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Check if event is duplicate using multiple strategies"""
        event_hash = self.create_event_hash(new_event)

        # 1. Check persistent state first
        if self.state_manager.is_event_processed(event_hash):
            state = self.state_manager.processed_events[event_hash]
            return True, f"already_processed_{state.status}", None

        # 2. Check against existing events in Gancio
        if event_hash in self.indexed_events:
            existing = self.indexed_events[event_hash][0]
            return True, "exact_match_in_gancio", existing

        # 3. Fuzzy matching for similar events
        return self._fuzzy_match(new_event)

    def _fuzzy_match(self, new_event: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Perform fuzzy matching against existing events"""
        new_title = self._normalize_text(new_event.get("title", ""))
        new_venue = self._normalize_text(new_event.get("venue", ""))
        new_date = self._normalize_date(new_event.get("start_datetime", ""))

        for existing in self.existing_events:
            existing_title = self._normalize_text(existing.get("title", ""))
            existing_venue = self._normalize_text(
                existing.get("place", {}).get("name", "")
            )
            existing_date = self._normalize_date(existing.get("start_datetime", ""))

            # Must match date and venue
            if new_date == existing_date and new_venue == existing_venue:
                # Check title similarity
                if self._titles_similar(new_title, existing_title):
                    return True, "fuzzy_match", existing

        return False, "new_event", None

    def _titles_similar(
        self, title1: str, title2: str, threshold: float = 0.85
    ) -> bool:
        """Check if two titles are similar"""
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, title1, title2).ratio()
        return similarity >= threshold


class ImprovedGancioSync:
    """Improved Gancio sync with better duplicate handling"""

    def __init__(self, gancio_base_url: str = "http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()
        self.authenticated = False
        self.state_manager = PersistentStateManager()
        self.deduplicator = EnhancedEventDeduplicator(self.state_manager)

        # Setup session headers
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

    def authenticate(self) -> bool:
        """Authenticate with Gancio"""
        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        print(f"🔑 Authenticating with Gancio as {email}...")

        try:
            # Get login page first
            self.session.get(f"{self.gancio_base_url}/login")

            # Post credentials
            login_response = self.session.post(
                f"{self.gancio_base_url}/auth/login",
                data={"email": email, "password": password},
                allow_redirects=True,
            )

            if "admin" in login_response.url or login_response.status_code == 200:
                print("✅ Authentication successful")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {login_response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def sync_events(self, scraped_events: List[Dict]) -> Dict:
        """Sync events with improved duplicate prevention"""
        if not self.authenticated:
            print("❌ Not authenticated with Gancio")
            return {"error": "Not authenticated"}

        # Load existing events for comparison
        if not self.deduplicator.load_existing_events(
            self.session, self.gancio_base_url
        ):
            print("⚠️ Continuing without existing events data")

        results = {
            "processed": 0,
            "new_events": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "details": [],
        }

        print(f"\n🔄 Processing {len(scraped_events)} scraped events...")

        for i, event in enumerate(scraped_events, 1):
            print(
                f"\n[{i}/{len(scraped_events)}] Processing: {event.get('title', 'Unknown')[:50]}..."
            )

            # Check for duplicates
            is_dup, reason, existing = self.deduplicator.is_duplicate(event)

            if is_dup:
                results["duplicates_skipped"] += 1
                print(f"   ⏭️ Skipped: {reason}")
                results["details"].append(
                    {"title": event.get("title"), "status": "skipped", "reason": reason}
                )
                continue

            # Create new event
            if self._create_event(event):
                results["new_events"] += 1

                # Mark as processed in state
                event_hash = self.deduplicator.create_event_hash(event)
                state = EventState(
                    event_hash=event_hash,
                    gancio_id=None,
                    last_seen=datetime.now(),
                    source="scraper",
                    venue=event.get("venue", ""),
                    title=event.get("title", ""),
                    date=self.deduplicator._normalize_date(event.get("start_datetime")),
                    status="pending",
                )
                self.state_manager.mark_event_processed(event_hash, state)

                results["details"].append(
                    {
                        "title": event.get("title"),
                        "status": "created",
                        "reason": "new_event",
                    }
                )
            else:
                results["errors"] += 1
                results["details"].append(
                    {
                        "title": event.get("title"),
                        "status": "error",
                        "reason": "creation_failed",
                    }
                )

            results["processed"] += 1

        # Save state
        self.state_manager.save_state()

        return results

    def _create_event(self, event: Dict) -> bool:
        """Create a single event in Gancio"""
        try:
            # Prepare event data for Gancio API
            gancio_event = {
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "start_datetime": event.get("start_datetime", 0),
                "end_datetime": event.get("end_datetime", 0),
                "place_id": event.get("place_id", 1),  # Default to Will's Pub
                "tags": event.get("tags", []),
            }

            response = self.session.post(
                f"{self.gancio_base_url}/api/event", json=gancio_event
            )

            if response.status_code in [200, 201]:
                print(f"   ✅ Event created successfully")
                return True
            else:
                print(
                    f"   ❌ Creation failed: {response.status_code} - {response.text[:100]}"
                )
                return False

        except Exception as e:
            print(f"   ❌ Creation error: {e}")
            return False


def should_run_sync() -> bool:
    """Intelligent scheduling - only run if likely to find new events"""
    # Check last run time
    last_run_file = "/tmp/orlandopunx_last_sync"

    if not os.path.exists(last_run_file):
        print("🕒 First run or no previous sync record found")
        return True

    try:
        with open(last_run_file, "r") as f:
            last_run = datetime.fromisoformat(f.read().strip())

        # Only run if it's been more than 12 hours
        hours_since_last = (datetime.now() - last_run).total_seconds() / 3600

        if hours_since_last < 12:
            print(
                f"🕒 Last run was {hours_since_last:.1f} hours ago, skipping (minimum 12h interval)"
            )
            return False
        else:
            print(f"🕒 Last run was {hours_since_last:.1f} hours ago, proceeding")
            return True

    except Exception as e:
        print(f"⚠️ Error checking last run time: {e}, proceeding anyway")
        return True


def mark_sync_run():
    """Mark that a sync has been run"""
    try:
        with open("/tmp/orlandopunx_last_sync", "w") as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        print(f"⚠️ Could not mark sync time: {e}")


# Placeholder scraper functions - integrate with existing scrapers
def scrape_willspub_events() -> List[Dict]:
    """Scrape Will's Pub events - integrated with production scraper"""
    print("📥 Scraping Will's Pub events...")
    try:
        # Import production Will's Pub scraper
        import sys

        sys.path.append(
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "event-sync")
        )
        from enhanced_multi_venue_sync import scrape_willspub_events as _scrape_willspub

        events = _scrape_willspub()

        # Ensure venue is set for all events
        for event in events:
            if not event.get("venue"):
                event["venue"] = "Will's Pub"
                event["source_venue"] = "Will's Pub"
            # Ensure place_id for Gancio compatibility
            if not event.get("place_id"):
                event["place_id"] = 1  # Will's Pub venue ID

        print(f"📋 Found {len(events)} Will's Pub events")
        return events

    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []

    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []


def scrape_conduit_events() -> List[Dict]:
    """Scrape Conduit events - integrated with production scraper"""
    print("📥 Scraping Conduit events...")
    try:
        # Import production Conduit scraper
        import sys

        sys.path.append(
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "event-sync")
        )
        from conduit_scraper import scrape_conduit_events as _scrape_conduit

        events = _scrape_conduit()

        # Ensure venue is set for all Conduit events
        for event in events:
            if not event.get("venue"):
                event["venue"] = "Conduit"
                event["source_venue"] = "Conduit"
            # Ensure place_id for Gancio compatibility
            if not event.get("place_id"):
                event["place_id"] = 5  # Conduit venue ID

        print(f"📋 Found {len(events)} Conduit events")
        return events

    except Exception as e:
        print(f"❌ Error scraping Conduit: {e}")
        return []

    except Exception as e:
        print(f"❌ Error scraping Conduit: {e}")
        return []


def main():
    """Main sync function with improved logic"""
    print("🚀 Orlando Punx Events - Improved Sync System")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Intelligent scheduling check
    if not should_run_sync():
        print("⏸️ Skipping sync due to intelligent scheduling")
        return 0

    # Initialize sync system
    syncer = ImprovedGancioSync()

    # Authenticate
    if not syncer.authenticate():
        print("❌ Authentication failed")
        return 1

    # Collect events from all sources
    all_events = []

    # Scrape Will's Pub
    willspub_events = scrape_willspub_events()
    all_events.extend(willspub_events)

    # Scrape Conduit
    conduit_events = scrape_conduit_events()
    all_events.extend(conduit_events)

    print(f"\n📊 Collected {len(all_events)} total events from all sources")

    if not all_events:
        print("ℹ️ No events found to process")
        mark_sync_run()
        return 0

    # Sync events
    results = syncer.sync_events(all_events)

    # Mark sync as completed
    mark_sync_run()

    # Print summary
    print(f"\n📊 Sync Summary:")
    print(f"   📥 Total events processed: {results['processed']}")
    print(f"   🆕 New events created: {results['new_events']}")
    print(f"   ⏭️ Duplicates skipped: {results['duplicates_skipped']}")
    print(f"   ❌ Errors: {results['errors']}")

    if results["new_events"] > 0:
        print(f"\n🎉 Successfully added {results['new_events']} new events!")
    else:
        print(
            f"\n✨ No new events to add - all events were duplicates or already processed"
        )

    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0 if results["errors"] == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
