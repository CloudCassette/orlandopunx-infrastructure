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
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

# Ensure the repo root is importable: the runner executes this file
# directly as `python3 fixed_sync_improved.py` from src/sync/, so
# `src.scrapers.*` is not on sys.path by default.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


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

    def resolve_place_id(self, name: str) -> Optional[int]:
        """Resolve a Gancio place id for an Orlando Weekly venue name.

        Priority:
          1. Environment override (`ORLANDO_WEEKLY_STARDUST_PLACE_ID` /
             `ORLANDO_WEEKLY_MSH_PLACE_ID`)
          2. Fuzzy match against the `places` table in self.db_path
             (e.g. `name LIKE '%sister%house%'`, `'%stardust%'`)

        Never falls back to Will's Pub (place 1): an event at the wrong
        venue is worse than no event. Returns None when unresolved so the
        caller can drop the event safely.
        """
        name = (name or "").strip()
        lower = name.lower()
        env_key = None
        pattern = None
        if "sister" in lower and "house" in lower:
            env_key = "ORLANDO_WEEKLY_MSH_PLACE_ID"
            pattern = "%sister%house%"
        elif "stardust" in lower:
            env_key = "ORLANDO_WEEKLY_STARDUST_PLACE_ID"
            pattern = "%stardust%"
        if not pattern:
            print(f"   ⚠️ No place resolution rule for venue: {name}")
            return None

        # 1) Explicit environment override
        override = os.environ.get(env_key, "")
        if override and override.strip().isdigit():
            place_id = int(override.strip())
            print(f"   🏢 {name} -> place_id {place_id} (env override)")
            return place_id

        # 2) Fuzzy lookup in the Gancio DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM places WHERE lower(name) LIKE ? "
                "ORDER BY id",
                (pattern,),
            )
            rows = cursor.fetchall()
            conn.close()
            if rows:
                place_id, place_name = rows[0]
                print(f"   🏢 {name} -> place_id {place_id} ({place_name})")
                return place_id
        except Exception as e:
            print(f"   ⚠️ Could not resolve place for {name}: {e}")

        print(
            f"   ⚠️ No Gancio place found for {name!r} — its events will "
            f"be dropped. Create the venue in the Gancio admin or set "
            f"{env_key}."
        )
        return None

    def fetch_orlando_weekly_events(self) -> List[Dict]:
        """Fetch Orlando Weekly events (Stardust + My Sister's House).

        Requires `playwright`. When it is missing (or scraping fails) a
        clear warning is printed and [] is returned so the Will's Pub
        sync still runs. Events are dropped when their Gancio place id
        cannot be resolved (safer than assigning the wrong venue).
        """
        print("\n🗓️ Fetching Orlando Weekly events...")
        try:
            from src.scrapers.orlando_weekly import (
                scrape_my_sisters_house_events,
                scrape_stardust_events,
            )
        except ImportError as e:
            print(
                f"   ⚠️ Orlando Weekly scraper unavailable "
                f"(playwright not installed?): {e}"
            )
            print("   Skipping Orlando Weekly — run `pip install playwright`")
            return []

        all_events: List[Dict] = []
        sources = [
            ("Stardust Video & Coffee", scrape_stardust_events),
            ("My Sister's House", scrape_my_sisters_house_events),
        ]

        for venue_name, fetcher in sources:
            try:
                raw_events = fetcher() or []
            except Exception as e:
                print(
                    f"   ❌ Orlando Weekly scraper failed for "
                    f"{venue_name}: {e}"
                )
                raw_events = []

            if not raw_events:
                print(f"   ℹ️ {venue_name}: 0 events fetched")
                continue

            place_id = self.resolve_place_id(venue_name)
            if place_id is None:
                print(
                    f"   ⚠️ Dropping {len(raw_events)} {venue_name} events "
                    f"(no place id)"
                )
                continue

            count = 0
            for ev in raw_events:
                title = ev.get("title", "")
                event_date = ev.get("date", "")
                event_time = ev.get("time") or "20:00"
                if not title or not event_date:
                    print(f"   ⏭️ Dropping incomplete event: {title!r}")
                    continue
                all_events.append({
                    "title": title,
                    "venue": venue_name,
                    "date": event_date,
                    "time": event_time[:5],
                    "description": (ev.get("description") or "")[:500],
                    "tags": ["orlando-weekly"],
                    "place_id": place_id,
                    "url": ev.get("url", ""),
                    "image_url": ev.get("image_url") or "",
                })
                count += 1
            print(f"   ✅ {venue_name}: {count} events ready")

        return all_events

    def _valid_flyer_url(self, url: str) -> bool:
        """Check a flyer URL is reachable and serves an image.

        HTTP GET with stream=True (headers only — the body is never
        downloaded), 10s timeout, no redirects. True only when the
        status is 200 and content-type starts with "image/". Returns
        False on any exception or mismatch, so a flaky CDN never blocks
        event creation.
        """
        if not url:
            return False
        try:
            r = requests.get(
                url, stream=True, timeout=10, allow_redirects=False
            )
            try:
                if r.status_code != 200:
                    return False
                content_type = (r.headers.get("content-type") or "").lower()
                return content_type.startswith("image/")
            finally:
                r.close()
        except Exception:
            return False

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
            image_url = event.get("image_url") or ""
            flyer_suffix = (
                " + flyer"
                if image_url and self._valid_flyer_url(image_url)
                else " (no flyer)"
            )
            print(
                f"   🧪 DRY RUN - Would submit: "
                f"{event.get('title', 'Unknown')}{flyer_suffix}"
            )
            return True

        # Event is unique, prepare for submission
        print(f"   📤 Submitting new event: {event.get('title', 'Unknown')}")
        
        try:
            # Convert date/time to datetime object. Scraper dates/times are
            # Orlando venue-local wall clock (America/New_York); Gancio's API
            # stores Unix epoch seconds (matching what /api/events returns).
            event_datetime = datetime.strptime(
                f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M"
            )
            end_datetime = event_datetime + timedelta(hours=3)

            ny_tz = ZoneInfo("America/New_York")
            gancio_event = {
                "title": event.get("title"),
                "description": event.get("description", ""),
                "start_datetime": int(
                    event_datetime.replace(tzinfo=ny_tz).timestamp()
                ),
                "end_datetime": int(
                    end_datetime.replace(tzinfo=ny_tz).timestamp()
                ),
                "place_id": event.get("place_id", 1),
                "tags": event.get("tags", []),
            }

            # Attach flyer when the image URL is reachable. Gancio's API
            # accepts image_url / image_name in the SAME JSON body and
            # downloads the image server-side (axios + sharp), so no
            # upload step is needed here.
            image_url = event.get("image_url") or ""
            payload = gancio_event
            if image_url and self._valid_flyer_url(image_url):
                payload = dict(gancio_event)
                payload["image_url"] = image_url
                payload["image_name"] = event.get("title", "")
            else:
                print(
                    f"   ⚠️ skipping flyer for "
                    f"{event.get('title', 'Unknown')} "
                    f"(missing or unreachable image)"
                )

            response = self.session.post(
                f"{self.gancio_base_url}/api/event",
                json=payload
            )

            # A 400 could be Gancio's sharp step rejecting the image;
            # retry once without the image fields so the event still
            # gets created.
            if response.status_code == 400 and "image_url" in payload:
                payload = dict(gancio_event)
                print(
                    f"   ⚠️ Retrying {event.get('title', 'Unknown')} "
                    f"without flyer (Gancio rejected image, HTTP 400)"
                )
                response = self.session.post(
                    f"{self.gancio_base_url}/api/event",
                    json=payload
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
        
        # Load ALL existing events (including unconfirmed). Fail closed:
        # if the dedup database cannot be read, refuse to submit anything —
        # submitting against an empty dedup index would re-post every event
        # (flooding the approval queue).
        dedup_ok = self.load_all_existing_events()
        dry_run = os.environ.get("DRY_RUN", "").lower() in {"1", "true", "yes"}
        if not dedup_ok and not dry_run:
            print(
                "❌ Dedup database unavailable — aborting ALL submissions "
                "to avoid duplicate posts"
            )
            return False
        
        # Fetch events from various sources
        all_events = []
        
        # Fetch from Will's Pub
        willspub_events = self.fetch_willspub_events()
        all_events.extend(willspub_events)
        print(f"   🎸 Will's Pub: {len(willspub_events)} events")

        # Fetch from Orlando Weekly (Stardust Video & Coffee + My Sister's House)
        ow_events = self.fetch_orlando_weekly_events()
        all_events.extend(ow_events)
        stardust_count = sum(
            1 for e in ow_events if e.get("venue") == "Stardust Video & Coffee"
        )
        msh_count = sum(
            1 for e in ow_events if e.get("venue") == "My Sister's House"
        )
        print(
            f"   🗓️ Orlando Weekly: {len(ow_events)} events "
            f"(Stardust: {stardust_count}, My Sister's House: {msh_count})"
        )
        
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
