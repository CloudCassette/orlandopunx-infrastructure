#!/usr/bin/env python3
"""
Orlando Weekly event scraper (CitySpark widget on orlandoweekly.com)
====================================================================

Scrapes upcoming events for two Orlando venues published in Orlando
Weekly's CitySpark-powered events calendar:

1. Stardust Video & Coffee
2. My Sister's House (Winter Park, FL)

Surfaces (verified against the live DOM on 2026-10-15):

* Both pages sit behind a JS proof-of-work anti-bot challenge
  ("Checking your browser..."). A Playwright Chromium context with a
  realistic user agent and a tiny stealth init script
  (navigator.webdriver -> undefined) clears it reliably.

* The old `community.orlandoweekly.com/location/stardust-video-and-coffee-2290117`
  venue page 301-redirects to the generic `https://www.orlandoweekly.com/events/`
  listing and is NOT scrapable, so Stardust is fetched from the CitySpark
  search surface instead (same widget the venue page used to embed).
  The scraper still *tries* the location URL first in case it is ever
  restored, and falls back to the search URL automatically.

* The My Sister's House content has no dedicated venue page either; it is
  fetched from the CitySpark search widget at
  https://www.orlandoweekly.com/events/show/?search=My+Sister%27s+House&format=all
  Search results are matched on TITLE or DESCRIPTION too, so cards are
  filtered to those whose venue text mentions the target venue
  (normalized: lowercase, punctuation stripped). Events hosted elsewhere
  (e.g. "Mood Lounge") are excluded.

Extraction is DOM-based. Card structure observed in the rendered widget:

    <div class="csEvWrap csEventTile ..." data-date="2026-10-18T00:00:00Z">
      <a href="/events/details/{slug}/{pid}/2026-10-18T19">
        <div class="csEventInfo">
          <div class="csMainInfo">
            <div class="csOneLine">Title</div>
            <div class="cityVenue">Venue | City, ST</div>
            <div class="csIconRow">...<svg/> 7:00 pm</div>
            <div class="csEventDescription">...</div>   (usually absent)
          </div>
          <div class="csIconInfo">...</div>
        </div>
      </a>
    </div>

* date: `data-date` attribute (concrete start date) or the detail URL
  `.../{pid}/YYYY-MM-DDTh`
* time: text of the first time-like string in `.csMainInfo .csIconRow`
  (e.g. "7:00 pm"), falling back to the trailing hour in the detail URL
* title: `.csOneLine` text
* venue text: `.cityVenue` text (used for filtering)
* url: the event's own detail URL on orlandoweekly.com
* description: the list DOM usually does not render one, so the scraper
  also captures the CitySpark JSON the widget itself fetches from
  portal.cityspark.com and merges each card's Summary/Description by PId
  (the numeric id embedded in the detail URL). If capture fails the
  description is simply left empty.

* image_url: the event flyer comes from the same CitySpark API payload
  — MediumImg, falling back to LargeImg, then the first entry of
  Images[].url, skipping placeholder ("default") and CitySpark logo
  URLs. Left as an empty string when the record is missing or has no
  usable image.

Each page-scrape function returns `[]` (with a printed ❌ note) instead of
raising on network/parse failures, so callers never break.

Standalone usage:
    python src/scrapers/orlando_weekly.py
"""

import re
import sys
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = "https://www.orlandoweekly.com"
CITYSPARK_API_PREFIX = "https://portal.cityspark.com/api/events/GetEvents/"

# The old location page survives as a 301 -> /events/; keep it as a first
# attempt so the scraper picks it up automatically if OW ever restores it.
STARDUST_URLS = [
    "https://community.orlandoweekly.com/location/stardust-video-and-coffee-2290117",
    "https://www.orlandoweekly.com/events/show/?search=Stardust+Video&format=all",
]
MY_SISTERS_HOUSE_URL = (
    "https://www.orlandoweekly.com/events/show/"
    "?search=My+Sister%27s+House&format=all"
)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
)

# Minimal stealth: hides Playwright's automation flag from the anti-bot
# challenge. Without this the JS PoW challenge never clears.
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
"""

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(am|pm)", re.IGNORECASE)
_LINK_DATE_RE = re.compile(r"/(\d{4}-\d{2}-\d{2})T(\d{1,2})/?$")
_RECURRING_RE = re.compile(
    r"\b(mondays?|tuesdays?|wednesdays?|thursdays?|fridays?|saturdays?|sundays?)\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace (for comparisons)."""
    if not text:
        return ""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _parse_12h_time(text: str):
    """Parse the first 'h:mm am/pm' in text -> 'HH:MM' or None."""
    m = _TIME_RE.search(text or "")
    if not m:
        return None
    hour, minute, period = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def _elt_text(el) -> str:
    """Best-effort inner text of a Playwright element."""
    try:
        if el is None:
            return ""
        return (el.inner_text() or "").strip()
    except Exception:
        return ""


def _flyer_url(rec) -> str:
    """Resolve a usable flyer URL from a CitySpark API record.

    Preference: MediumImg, LargeImg, then the first entry of
    Images[].url. URLs containing "default" or the CitySpark logo path
    ("citysparklogo") are treated as placeholders and skipped, matching
    the `default`-URL convention of the songkick scraper. Returns ""
    when the record is missing or no usable image exists.
    """
    if not rec:
        return ""
    candidates = [rec.get("MediumImg"), rec.get("LargeImg")]
    images = rec.get("Images") or []
    if isinstance(images, list):
        candidates += [
            img.get("url") for img in images if isinstance(img, dict)
        ]
    for url in candidates:
        url = (url or "").strip()
        low = url.lower()
        if url and "default" not in low and "citysparklogo" not in low:
            return url
    return ""


def _extract_cards(page, venue_keywords, venue_name, api_records):
    """Extract + filter + normalize event cards from the rendered widget DOM.

    Cards are matched on their `.cityVenue` text (not the title) so that
    search hits on other venues (the widget matches titles/descriptions
    too) are excluded. Returns canonical-ish dicts:
        title, date (YYYY-MM-DD | None), time (HH:MM | None), venue,
        description, url, pid, raw_venue_text, image_url ("" | flyer URL)
    """
    events = []
    seen = set()
    wraps = page.query_selector_all(".csEvWrap")
    for wrap in wraps:
        try:
            title = _elt_text(wrap.query_selector(".csOneLine"))
            venue_text = _elt_text(wrap.query_selector(".cityVenue"))
            if not title:
                continue

            # --- venue filter ---
            norm_venue = _normalize(venue_text)
            if not any(kw in norm_venue for kw in venue_keywords):
                print(
                    f"   ⏭️ EXCLUDED (different venue): {title[:60]!r} "
                    f"@ {venue_text[:60]!r}"
                )
                continue

            # --- link / pid / url ---
            href = ""
            a_el = wrap.query_selector("a[href]")
            if a_el is not None:
                href = a_el.get_attribute("href") or ""
            url = urljoin(BASE_URL, href) if href else BASE_URL
            pid = None
            m = re.search(r"/events/details/[^/]+/(\d+)", href or "")
            if m:
                pid = int(m.group(1))

            # --- date ---
            date = None
            d_attr = wrap.get_attribute("data-date") or ""
            if d_attr:
                date = d_attr[:10]
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                    date = None
            if not date:
                lm = _LINK_DATE_RE.search(href or "")
                if lm:
                    date = lm.group(1)

            # --- time ---
            time_str = None
            time_text = _elt_text(
                wrap.query_selector(".csMainInfo .csIconRow")
            )
            time_str = _parse_12h_time(time_text)
            if not time_str:
                lm = _LINK_DATE_RE.search(href or "")
                if lm:
                    time_str = f"{int(lm.group(2)):02d}:00"

            # --- recurring-only events (no concrete date) ---
            if not date:
                if _RECURRING_RE.search(time_text or "") and time_str is None:
                    print(
                        f"   ⏭️ SKIPPED (recurring pattern only): "
                        f"{title[:60]!r} — {time_text[:60]!r}"
                    )
                else:
                    print(
                        f"   ⏭️ SKIPPED (no concrete start date): "
                        f"{title[:60]!r}"
                    )
                continue

            # --- description via the widget's own API payload ---
            description = ""
            image_url = ""
            if pid and pid in api_records:
                rec = api_records[pid]
                description = (
                    rec.get("Summary")
                    or rec.get("Description")
                    or rec.get("Short")
                    or ""
                ).strip()
                image_url = _flyer_url(rec)
            else:
                # Some views render a description block directly
                desc_el = wrap.query_selector(".csEventDescription")
                description = _elt_text(desc_el)

            # --- dedupe within page (same normalized title + start date) ---
            key = (_normalize(title), date)
            if key in seen:
                print(f"   ⏭️ DEDUP (same title+date): {title[:60]!r} @ {date}")
                continue
            seen.add(key)

            events.append(
                {
                    "title": title,
                    "date": date,
                    "time": time_str,
                    "venue": venue_name,
                    "description": description[:500],
                    "url": url,
                    "pid": pid,
                    "raw_venue_text": venue_text,
                    "image_url": image_url,
                }
            )
        except Exception as e:
            print(f"   ❌ Error parsing card: {e}")
            continue
    return events


def _fetch_cards(urls, venue_keywords, venue_name):
    """Open the first URL that yields matching cards and extract events.

    Returns (events, used_url) on success, ([], None) on total failure —
    never raises.
    """
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1440, "height": 2300},
                locale="en-US",
                timezone_id="America/New_York",
            )
            context.add_init_script(STEALTH_JS)

            api_records = {}

            for url in urls:
                page = context.new_page()
                page.set_default_timeout(60000)

                def _on_response(resp, _records=api_records):
                    u = resp.url
                    if u.startswith(CITYSPARK_API_PREFIX):
                        try:
                            import json

                            body = resp.text()
                            data = json.loads(body)
                            for rec in data.get("Value") or []:
                                pid = rec.get("PId")
                                if pid is not None:
                                    _records[int(pid)] = rec
                        except Exception:
                            pass

                page.on("response", _on_response)

                try:
                    page.goto(
                        url, wait_until="domcontentloaded", timeout=60000
                    )
                except Exception as e:
                    print(f"   ❌ Navigation error for {url[:90]}: {e}")
                    continue

                # Let the anti-bot challenge resolve / widget render.
                try:
                    page.wait_for_load_state("networkidle", timeout=25000)
                except Exception:
                    pass
                page.wait_for_timeout(3000)
                try:
                    title = page.title()
                except Exception:
                    title = ""
                if "Checking your browser" in title:
                    # Poll for the JS challenge to clear (PoW + reload).
                    cleared = False
                    for _ in range(30):
                        page.wait_for_timeout(2000)
                        try:
                            if "Checking your browser" not in (
                                page.title() or ""
                            ):
                                cleared = True
                                break
                        except Exception:
                            pass
                    if not cleared:
                        print(
                            f"   ❌ Anti-bot challenge never cleared for "
                            f"{url[:90]}"
                        )
                        continue
                    try:
                        page.wait_for_load_state("networkidle", timeout=20000)
                    except Exception:
                        pass
                    page.wait_for_timeout(2000)

                # The old Stardust location page now 301s to /events/. A
                # redirected generic listing is NOT the location page (it
                # only shows a small slice of the combined calendar), so
                # detect the redirect and fall through to the next URL.
                try:
                    final_url = page.url
                except Exception:
                    final_url = url
                if (
                    "location/" in url
                    and "location/" not in final_url
                ):
                    print(
                        f"   ℹ️ Location page redirects to "
                        f"{final_url[:70]} — using search surface."
                    )
                    page.close()
                    continue

                # Wait for event cards to render.
                try:
                    page.wait_for_selector(
                        ".csEvWrap", timeout=30000
                    )
                except Exception:
                    print(
                        f"   ⚠️ No .csEvWrap cards rendered on {url[:90]}"
                    )

                events = _extract_cards(
                    page, venue_keywords, venue_name, api_records
                )
                page.close()
                if events:
                    browser.close()
                    return events, url
                print(
                    f"   ⚠️ No '{venue_name}' cards on {url[:90]} — "
                    f"trying next surface."
                )

            browser.close()
            return [], None
    except Exception as e:
        print(f"   ❌ Orlando Weekly scraping failed: {e}")
        return [], None


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def scrape_stardust_events():
    """Upcoming Stardust Video & Coffee events (title/date/time/venue/url)."""
    print("🗓️ Scraping Orlando Weekly — Stardust Video & Coffee...")
    events, used = _fetch_cards(
        STARDUST_URLS,
        ["stardust"],
        "Stardust Video & Coffee",
    )
    print(f"   ✅ Found {len(events)} Stardust events")
    return events


def scrape_my_sisters_house_events():
    """Upcoming My Sister's House events (Winter Park; venue-text filtered)."""
    print("🗓️ Scraping Orlando Weekly — My Sister's House...")
    events, used = _fetch_cards(
        [MY_SISTERS_HOUSE_URL],
        ["my sisters house"],
        "My Sister's House",
    )
    print(f"   ✅ Found {len(events)} My Sister's House events")
    return events


def _fmt_event(ev):
    t = ev.get("time") or "--:--"
    return (
        f"   • {ev.get('title', '')[:70]}\n"
        f"     {ev.get('date')} @ {t} · {ev.get('venue')}\n"
        f"     image_url: {ev.get('image_url') or '(none)'}\n"
        f"     {ev.get('url')}"
    )


if __name__ == "__main__":
    print("=" * 68)
    print("Orlando Weekly scraper — standalone run")
    print("=" * 68)

    stardust = scrape_stardust_events()
    print(f"\n🎸 STARDUST VIDEO & COFFEE ({len(stardust)} events):")
    for ev in stardust[:5]:
        print(_fmt_event(ev))

    msh = scrape_my_sisters_house_events()
    print(f"\n🏠 MY SISTER'S HOUSE ({len(msh)} events):")
    for ev in msh[:5]:
        print(_fmt_event(ev))

    print(f"\n📊 Total: {len(stardust) + len(msh)} events")
    sys.exit(0)