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
        # Lazily-cached admin OAuth token (see _gancio_bearer_token).
        self._bearer_token = None

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
        """Fetch events from Will's Pub via the `src.scrapers.willspub` module.

        The homepage was rebuilt on TicketWeb markup (no more
        `tribe-events-*` classes); all selectors live in the scraper
        module. Guarded import (kept in the same style as the Orlando
        Weekly fetch) so a missing dependency never breaks the sync.
        """
        print("🎸 Fetching Will's Pub events...")
        try:
            from src.scrapers.willspub import scrape_willspub_events
        except ImportError as e:
            print(f"   ⚠️ Will's Pub scraper unavailable: {e}")
            return []

        try:
            raw_events = scrape_willspub_events(download_images=False)
        except Exception as e:
            print(f"   ❌ Will's Pub scraper failed: {e}")
            return []

        events = []
        for ev in raw_events:
            title = ev.get("title", "")
            event_date = ev.get("date", "")
            event_time = ev.get("time") or "20:00"
            if not title or not event_date:
                print(f"   ⏭️ Dropping incomplete Will's Pub event: {title!r}")
                continue
            flyer_url = ev.get("flyer_url") or ""
            events.append({
                "title": title,
                "venue": "Will's Pub",
                "date": event_date,
                "time": event_time[:5],
                "description": (ev.get("description") or "")[:500],
                "tags": ["punk", "live-music"],
                "place_id": 1,  # Will's Pub venue ID in Gancio
                "url": ev.get("url", ""),
                # Attach the flyer only when the URL is reachable and
                # really serves an image (flaky CDNs must not block
                # event creation).
                "image_url": flyer_url
                if self._valid_flyer_url(flyer_url)
                else "",
            })

        print(f"   ✅ Found {len(events)} events from Will's Pub")
        return events

    def fetch_conduit_events(self) -> List[Dict]:
        """Fetch events from Conduit via the `src.scrapers.conduit` module.

        conduitfl.com also runs TicketWeb markup; selectors live in the
        scraper module. Guarded import, same style as the other fetchers.
        """
        print("🎸 Fetching Conduit events...")
        try:
            from src.scrapers.conduit import scrape_conduit_events
        except ImportError as e:
            print(f"   ⚠️ Conduit scraper unavailable: {e}")
            return []

        try:
            raw_events = scrape_conduit_events(download_images=False)
        except Exception as e:
            print(f"   ❌ Conduit scraper failed: {e}")
            return []

        events = []
        for ev in raw_events:
            title = ev.get("title", "")
            event_date = ev.get("date", "")
            event_time = ev.get("time") or "20:00"
            if not title or not event_date:
                print(f"   ⏭️ Dropping incomplete Conduit event: {title!r}")
                continue
            flyer_url = ev.get("flyer_url") or ""
            events.append({
                "title": title,
                "venue": "Conduit",
                "date": event_date,
                "time": event_time[:5],
                "description": (ev.get("description") or "")[:500],
                "tags": ["punk"],
                "place_id": 5,  # Conduit venue ID in Gancio
                "url": ev.get("url", ""),
                "image_url": flyer_url
                if self._valid_flyer_url(flyer_url)
                else "",
            })

        print(f"   ✅ Found {len(events)} events from Conduit")
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
                url,
                stream=True,
                timeout=10,
                allow_redirects=False,
                # willspub.org (flyer host for a few Will's Pub events)
                # 403s requests without a browser UA — verified on the
                # server 2026-10-16. Harmless for the other flyer hosts
                # (i.ticketweb.com, citysparkstorage).
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
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

    def _gancio_bearer_token(self, force: bool = False) -> Optional[str]:
        """Admin OAuth bearer token for Gancio's API (lazily cached).

        Logs in with the password grant (`grant_type=password`,
        `client_id=self`, form-encoded body — Gancio v1.4.4) and caches
        the opaque access_token for authorized admin calls. Pass
        ``force=True`` to discard the cache and re-login (used to
        recover from a single 401). Returns None when credentials are
        missing/empty or the login fails — callers treat that as "admin
        calls disabled" and continue without one.
        """
        if not force and self._bearer_token:
            return self._bearer_token

        email = os.environ.get("GANCIO_EMAIL", "admin")
        password = os.environ.get("GANCIO_PASSWORD", "")
        if not email or not password:
            print(
                "   ℹ️ GANCIO_EMAIL/GANCIO_PASSWORD not set — "
                "admin API calls (flyer re-attach) disabled"
            )
            self._bearer_token = None
            return None

        try:
            response = self.session.post(
                f"{self.gancio_base_url}/oauth/login",
                data={
                    "grant_type": "password",
                    "username": email,
                    "password": password,
                    "client_id": "self",
                },
                timeout=20,
            )
            if response.status_code != 200:
                print(
                    f"   ⚠️ Gancio OAuth login failed: "
                    f"HTTP {response.status_code}"
                )
                self._bearer_token = None
                return None
            token = response.json().get("access_token")
            if not token:
                print("   ⚠️ Gancio OAuth login returned no access_token")
                self._bearer_token = None
                return None
            self._bearer_token = token
            return token
        except Exception as e:
            print(f"   ⚠️ Gancio OAuth login error: {e}")
            self._bearer_token = None
            return None

    def _assure_flyer_attached(self, response, image_url: str) -> None:
        """Flyer assurance: re-attach a flyer Gancio silently dropped.

        Event POSTs already carry ``image_url`` in the body, but Gancio
        occasionally accepts the event yet ends up with an empty
        ``media`` array (observed against v1.4.4). When that happens the
        same URL is re-attached via ``PUT /api/event`` so the server
        downloads and processes the image again. The event exists either
        way, so a failed attach is only logged — never retried beyond
        the single 401 re-login.
        """
        if not image_url:
            return

        try:
            body = response.json()
        except ValueError:
            print(
                "   ℹ️ could not read created-event body — "
                "cannot verify flyer media"
            )
            return
        if not isinstance(body, dict):
            return
        if body.get("media"):
            # Flyer landed in-band — nothing to do.
            return

        event_id = body.get("id")
        if event_id is None:
            print(
                "   ℹ️ created-event body has no id — cannot "
                "re-attach flyer"
            )
            return

        token = self._gancio_bearer_token()
        if not token:
            print(
                f"   ℹ️ media may be missing for id={event_id}: "
                f"set GANCIO_EMAIL/GANCIO_PASSWORD so the flyer "
                f"can be re-attached"
            )
            return

        # Gancio v1.4.4's PUT /api/event is not a sparse patch: a missing
        # `description` crashes linkifyHtml (-> HTTP 400), and
        # `place_name`/`tags` are rewritten unconditionally, so omitting
        # them would repoint the event to a new/empty place or wipe its
        # tags. Build the body from the created event's own response.
        place = body.get("place") or {}
        tag_names = [
            t.get("tag") if isinstance(t, dict) else str(t)
            for t in (body.get("tags") or [])
        ]
        place_name = place.get("name") or ""
        if not place_name:
            print(
                f"   ⚠️ flyer attach skipped for id={event_id}: "
                f"no place_name in event body (PUT would repoint venue)"
            )
            return
        put_body = {
            "id": event_id,
            "description": body.get("description") or "",
            "place_name": place_name,
            "tags": tag_names,
            "image_url": image_url,
        }

        def _put():
            return self.session.put(
                f"{self.gancio_base_url}/api/event",
                json=put_body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )

        put_response = _put()
        # Token expired mid-run: re-login once and retry the PUT.
        if put_response.status_code == 401:
            token = self._gancio_bearer_token(force=True)
            if token:
                put_response = _put()

        if put_response.status_code < 300:
            print(f"   🔧 flyer re-attached (id={event_id})")
        else:
            print(
                f"   ⚠️ flyer attach failed ({put_response.status_code}): "
                f"{put_response.text[:160]}"
            )

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
                # Flyer assurance: the POST body carried `image_url`, but
                # Gancio sometimes creates the event with an empty media
                # array. Re-attach via PUT when the response shows none.
                self._assure_flyer_attached(response, image_url)
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

        # Fetch from Conduit
        conduit_events = self.fetch_conduit_events()
        all_events.extend(conduit_events)
        print(f"   🎸 Conduit: {len(conduit_events)} events")
        
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
