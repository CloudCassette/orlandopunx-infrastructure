#!/usr/bin/env python3
"""
Backfill missing event flyers from Orlando Weekly
==================================================

One-off tooling for the approval queue: fetches Gancio's unconfirmed
(future, pending) events, picks the ones whose ``media`` array is empty,
and looks each one up on Orlando Weekly's search widget to recover a
flyer URL. Found flyers are attached to the existing event via
``PUT /api/event`` (``{"id": ..., "image_url": ...}``) with an admin
OAuth bearer token.

Flow:
    1. OAuth login (password grant, ``client_id=self``) against the
       Gancio instance configured in the env file.
    2. ``GET /api/event/unconfirmed`` -> events without media.
    3. Per event: ``search_orlando_weekly_events(title, venue_keywords,
       date_str)`` (the widget search never raises) and attach the flyer
       when one comes back.

Robustness: a failure on any single event is counted ("failed") and the
script continues; only a total login failure (or missing config) aborts
with exit code 1.

Usage:
    python3 scripts/backfill-flyers.py                        # dry run
    python3 scripts/backfill-flyers.py --apply                # attach
    python3 scripts/backfill-flyers.py --env-file /path/.env --apply
    python3 scripts/backfill-flyers.py --base-url http://... --email x --password y

Dry run is the default and only prints what WOULD be attached.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

# Ensure the repo root is importable so `src.scrapers.*` resolves when
# this script is run directly as `python3 scripts/backfill-flyers.py`.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Imported lazily below with a clear error: the search helper needs
# playwright + Chromium, which is only installed in the sync venv.
_search_orlando_weekly_events = None


def _get_search():
    """Import the Orlando Weekly search helper (guarded for missing deps)."""
    global _search_orlando_weekly_events
    if _search_orlando_weekly_events is None:
        try:
            from src.scrapers.orlando_weekly import (
                search_orlando_weekly_events,
            )
        except ImportError as e:
            print(
                f"❌ Orlando Weekly search unavailable (playwright "
                f"installed?): {e}"
            )
            raise
        _search_orlando_weekly_events = search_orlando_weekly_events
    return _search_orlando_weekly_events


def parse_env_file(path: str) -> dict:
    """Parse a KEY=VALUE env file (`#` comments and blanks ignored)."""
    values = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        print(f"⚠️ env file not found: {path}")
    return values


def venue_keywords(place_name: str) -> list:
    """Orlando Weekly search keywords for a Gancio place name.

    Known venues map to the keywords the scraper filters on; anything
    else falls back to the first two significant lowercase words of the
    name (punctuation stripped).
    """
    name = (place_name or "").strip().lower()
    if not name:
        return []
    if "stardust" in name:
        return ["stardust"]
    if "sister" in name and "house" in name:
        return ["my sisters house"]
    if "social" in name:
        return ["the social"]
    if "beacham" in name:
        return ["beacham"]
    if "abbey" in name:
        return ["the abbey"]
    if "conduit" in name:
        return ["conduit"]
    words = [
        w
        for w in re.sub(r"[^a-z0-9\s]", " ", name).split()
        if w and w not in {"the", "at", "of"}
    ]
    return words[:2] or [name]


def login(base_url: str, email: str, password: str):
    """OAuth password-grant login; returns the bearer token or None."""
    try:
        r = requests.post(
            f"{base_url}/oauth/login",
            data={
                "grant_type": "password",
                "username": email,
                "password": password,
                "client_id": "self",
            },
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"❌ Gancio OAuth login request failed: {e}")
        return None
    if r.status_code != 200:
        print(
            f"❌ Gancio OAuth login failed: HTTP {r.status_code} — "
            f"{r.text[:200]}"
        )
        return None
    try:
        token = r.json().get("access_token")
    except ValueError:
        token = None
    if not token:
        print("❌ Gancio OAuth login returned no access_token")
        return None
    return token


def event_date_str(start_datetime):
    """Format an event's start_datetime (unix) as YYYY-MM-DD, or None."""
    if start_datetime in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(start_datetime)).strftime(
            "%Y-%m-%d"
        )
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Backfill missing event flyers from Orlando Weekly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Dry run is the default: only prints what WOULD be attached. "
            "Pass --apply to attach for real."
        ),
    )
    parser.add_argument(
        "--env-file",
        default=os.path.expanduser("~/approval-app/.env"),
        help="KEY=VALUE env file with GANCIO_BASE/GANCIO_ADMIN_EMAIL/"
        "GANCIO_ADMIN_PASSWORD (default: ~/approval-app/.env)",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Override the Gancio base URL from the env file",
    )
    parser.add_argument(
        "--email",
        default="",
        help="Override the admin email from the env file",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Override the admin password from the env file",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        dest="apply",
        action="store_false",
        default=True,
        help="Only print what WOULD be attached (default)",
    )
    mode.add_argument(
        "--apply",
        dest="apply",
        action="store_true",
        help="Actually attach flyers",
    )
    args = parser.parse_args()

    env = parse_env_file(args.env_file)
    base_url = (args.base_url or env.get("GANCIO_BASE") or "").rstrip("/")
    email = args.email or env.get("GANCIO_ADMIN_EMAIL") or ""
    password = args.password or env.get("GANCIO_ADMIN_PASSWORD") or ""

    if not base_url:
        print(
            "❌ No Gancio base URL — set GANCIO_BASE in the env file "
            "or pass --base-url"
        )
        return 1
    if not email or not password:
        print(
            "❌ Missing admin credentials (GANCIO_ADMIN_EMAIL / "
            "GANCIO_ADMIN_PASSWORD in the env file, or --email/--password)"
        )
        return 1

    token = login(base_url, email, password)
    if not token:
        print("❌ Gancio login failed — aborting")
        return 1
    print("✅ OAuth login OK (bearer token acquired)")

    headers = {"Authorization": f"Bearer {token}"}
    session = requests.Session()

    r = session.get(
        f"{base_url}/api/event/unconfirmed", headers=headers, timeout=30
    )
    if r.status_code != 200:
        print(
            f"❌ GET /api/event/unconfirmed failed: HTTP {r.status_code} — "
            f"{r.text[:200]}"
        )
        return 1
    try:
        events = r.json()
    except ValueError:
        events = None
    if not isinstance(events, list):
        print(f"❌ Unexpected unconfirmed payload: {type(events).__name__}")
        return 1
    print(f"📋 {len(events)} unconfirmed events")

    candidates = [e for e in events if not (e.get("media") or [])]
    print(f"   → {len(candidates)} with no media (backfill candidates)")

    search = _get_search()

    keyword_cache = {}

    def keywords_for(event):
        place = event.get("place") or {}
        pname = place.get("name") or ""
        if pname not in keyword_cache:
            keyword_cache[pname] = venue_keywords(pname)
        return keyword_cache[pname]

    attached = not_found = failed = 0
    for ev in candidates:
        eid = ev.get("id")
        title = ev.get("title") or ""
        place = (ev.get("place") or {}).get("name") or "?"
        start = ev.get("start_datetime")
        date_str = event_date_str(start)
        keywords = keywords_for(ev)

        print(
            f"\n🔍 {title!r} @ {place} (id={eid}, "
            f"{date_str or 'no-date'})"
        )
        try:
            flyer = search(title, keywords, date_str)
        except Exception as e:
            print(f"   ❌ search failed: {e}")
            failed += 1
            continue

        if not flyer:
            print("   ℹ️ not-found — Orlando Weekly has no art for this")
            not_found += 1
            continue

        print(f"   🖼️ flyer: {flyer}")
        if not args.apply:
            print("   🧪 DRY RUN — would attach")
            attached += 1
            continue

        # Gancio v1.4.4 needs the full-ish body: missing description
        # crashes linkifyHtml (HTTP 400), and place_name/tags are
        # rewritten unconditionally — omit them and the venue may be
        # repointed or the tags wiped.
        place_name = (ev.get("place") or {}).get("name") or ""
        tag_names = [
            t.get("tag") if isinstance(t, dict) else str(t)
            for t in (ev.get("tags") or [])
        ]
        if not place_name:
            print(
                f"   ❌ attach failed: no place name in event payload "
                f"(id={eid})"
            )
            failed += 1
            continue
        try:
            put = session.put(
                f"{base_url}/api/event",
                json={
                    "id": eid,
                    "description": "",
                    "place_name": place_name,
                    "tags": tag_names,
                    "image_url": flyer,
                },
                headers=headers,
                timeout=60,
            )
        except requests.RequestException as e:
            print(f"   ❌ attach failed: {e}")
            failed += 1
            continue
        if put.status_code < 300:
            print(f"   ✅ attached (id={eid})")
            attached += 1
        else:
            print(
                f"   ❌ attach failed: HTTP {put.status_code} — "
                f"{put.text[:160]}"
            )
            failed += 1

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("\n" + "=" * 60)
    print(
        f"📊 Backfill summary ({mode}): "
        f"{attached} attached, {not_found} no art found, {failed} failed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())