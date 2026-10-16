#!/usr/bin/env python3
"""
🎸 Conduit FL Event Scraper (TicketWeb plugin markup)
=====================================================
Scrapes events from https://www.conduitfl.com/. The homepage uses
TicketWeb's plugin markup — one event per `div.tw-section`:

    <div class="tw-section">
      <div class="tw-event-datetime">
        <span class="tw-day-of-week">Fri</span>
        <span class="tw-event-date">10.16</span>
      </div>
      <div class="tw-image"><a href="/tm-event/...">
        <img class="event-img large" src="...flyer..."/></a></div>
      <div class="tw-name"> <a href="/tm-event/...">Title</a> </div>
      <div class="tw-date-time">
        <span class="tw-event-time-complete">
          <span class="tw-event-time">Show: 08:00PM</span>
        </span>
        <span class="tw-event-timezone">EDT</span>
        <span class="tw-event-door-time-complete">
          (Doors: <span class="tw-event-door-time">08:00PM</span>)
        </span>
      </div>
      <div class="tw-age-restriction">18 and up</div>
      <div class="tw-info-price-buy-tix">
        <span class="tw-price">$19.90</span> ...
      </div>
    </div>

Verified against the live page on 2026-10-16: 40 `.tw-section` blocks =
**20 unique events each rendered twice** (the plugin emits the list twice),
so results are deduplicated on (title, date).

Date format: day-of-week + `MM.DD` with NO year. The year is recovered
by matching the stated weekday against the current / next calendar year.

Selectors / structure may change without notice (they did once already) —
the `parse_conduit_events_from_html` function is the single place to
repair. Events without a parseable concrete date are logged + skipped.

Existing function names are kept for callers:
    scrape_conduit_events(download_images=True)
    parse_conduit_events_from_html(soup, url, headers, download_images=True)

Standalone usage:
    python src/scrapers/conduit.py
"""

import json
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CONDUIT_URL = "https://www.conduitfl.com/"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

_SKIP_PHRASES = [
    "More Info",
    "Buy Tickets",
    "Click here",
    "View Details",
    "Learn More",
    "Read More",
]

_DOW = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}
_MMDD_RE = re.compile(r"(\d{1,2})\.(\d{1,2})")
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*([AaPp][Mm])")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def clean_event_title(title):
    """Clean up an event title."""
    title = re.sub(r"\s+", " ", title or "").strip()
    title = re.sub(
        r"\s+(Show|Concert|Live|at Conduit)$", "", title, flags=re.IGNORECASE
    )
    title = re.sub(r"^.*?Presents:\s*", "", title, flags=re.IGNORECASE)
    return title.strip()


def should_skip_title(title):
    """Check if a title is UI boilerplate rather than an event name."""
    return any(phrase.lower() in (title or "").lower() for phrase in _SKIP_PHRASES)


def _to_24h(hour, minute, period):
    hour = int(hour)
    minute = int(minute)
    p = period.lower()
    if p == "pm" and hour != 12:
        hour += 12
    elif p == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def resolve_conduit_date(dow_text, mmdd_text):
    """Resolve 'Fri' + '10.16' (no year) to 'YYYY-MM-DD' or None.

    The weekday is verified against the calendar so a date near the
    year boundary (e.g. `12.30` shown in December) resolves to the
    correct *upcoming* year. Always picks the occurrence that is not
    more than 30 days in the past (next year is tried automatically).
    """
    if not mmdd_text:
        return None
    m = _MMDD_RE.search(mmdd_text.strip())
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    wanted = _DOW.get((dow_text or "").lower()[:3])

    now = datetime.now()
    candidates = [now.year, now.year + 1]
    if now.month == 1:  # january listings can still be last December's page
        candidates.insert(0, now.year - 1)

    best = None
    for year in candidates:
        try:
            dt = datetime(year, month, day)
        except ValueError:
            continue
        age = (now - dt).days
        if age > 30:  # too far in the past -> not an upcoming listing
            continue
        # Prefer a weekday match; if the stated weekday is unknown
        # (empty/missing), accept the nearest future date.
        if wanted is not None and dt.weekday() != wanted:
            continue
        score = age  # smaller age (nearer future) wins
        if best is None or score < best[0]:
            best = (score, dt)
    if best is None:
        return None
    return best[1].strftime("%Y-%m-%d")


def extract_event_flyer(section, base_url):
    """Flyer URL from the `.tw-image img` inside a section (or '')."""
    img = section.find("img", class_="event-img")
    if img and img.get("src"):
        return urljoin(base_url, img["src"].strip())
    return ""


def build_description(age_info, price):
    """Conduit has no description block on the list page — build one."""
    parts = ["Live music at Conduit."]
    if age_info:
        parts.append(age_info)
    if price:
        parts.append(f"Tickets: {price}")
    return " ".join(parts)


# --------------------------------------------------------------------------
# parsing (DOM-in, dicts-out — testable without network)
# --------------------------------------------------------------------------

def parse_conduit_events_from_html(soup, url, headers, download_images=True):
    """Parse Conduit events from a BeautifulSoup of the homepage.

    Returns a list of dicts:
        title, date (YYYY-MM-DD), time (HH:MM), venue, venue_url, url,
        description, price, age_restriction, source, flyer_url
    Deduplicated on (title, date) — the TicketWeb plugin renders the
    event list twice on the homepage.
    """
    events = []
    seen = set()
    sections = soup.find_all(class_="tw-section")
    if not sections:
        print("   ⚠️ No .tw-section event blocks found on Conduit page")
        return events

    for section in sections:
        try:
            name_el = section.find(class_="tw-name")
            if not name_el:
                continue
            a = name_el.find("a")
            raw_title = (
                a.get_text(strip=True) if a is not None
                else name_el.get_text(strip=True)
            )
            title = clean_event_title(raw_title)
            if not title or len(title) < 3 or should_skip_title(title):
                continue

            # All sections on the homepage are Conduit's own events, but
            # pin the venue anyway.
            venue_txt = section.find(class_="tw-venue-details")
            venue_name = venue_txt.get_text(" ", strip=True) if venue_txt else ""
            venue = venue_name or "Conduit"

            dow_el = section.find(class_="tw-day-of-week")
            dow_text = dow_el.get_text(strip=True) if dow_el else ""
            date_el = section.find(class_="tw-event-date")
            mmdd_text = date_el.get_text(strip=True) if date_el else ""

            event_date = resolve_conduit_date(dow_text, mmdd_text)
            if not event_date:
                print(
                    f"   ⏭️ SKIPPED (no parseable date): {title[:60]!r} — "
                    f"dow {dow_text!r}, date {mmdd_text!r}"
                )
                continue

            time_el = section.find(class_="tw-event-time")
            time_text = time_el.get_text(strip=True) if time_el else ""
            tm = _TIME_RE.search(time_text)
            event_time = _to_24h(tm.group(1), tm.group(2), tm.group(3)) if tm else "19:00"

            price_el = section.find(class_="tw-price")
            price = price_el.get_text(strip=True) if price_el else ""
            age_el = section.find(class_="tw-age-restriction")
            age = age_el.get_text(strip=True) if age_el else ""

            href = a.get("href") if a is not None else None
            event_url = urljoin(url, href) if href else url

            key = (title, event_date)
            if key in seen:
                print(f"   ⏭️ DEDUP (plugin renders list twice): {title[:50]!r} {event_date}")
                continue
            seen.add(key)

            events.append({
                "title": title,
                "date": event_date,
                "time": event_time,
                "venue": venue,
                "venue_url": url,
                "url": event_url,
                "description": build_description(age, price),
                "price": price,
                "age_restriction": age,
                "source": "conduit",
                "flyer_url": extract_event_flyer(section, url),
            })
            print(f"   ✅ {title} - {event_date} at {event_time}")
        except Exception as e:
            print(f"   ❌ Error parsing Conduit event: {e}")
            continue
    return events


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def scrape_conduit_events(download_images=True):
    """Scrape events from Conduit FL.

    `download_images` is accepted for signature compatibility; flyers are
    surfaced as URLs (the page already embeds them), so nothing is
    downloaded here.
    """
    print("🎸 Scraping Conduit FL events (TicketWeb markup)...")
    last_err = None
    for attempt, user_agent in enumerate(USER_AGENTS):
        headers = {
            "User-Agent": user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            if attempt > 0:
                time.sleep(2)
            response = requests.get(CONDUIT_URL, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            events = parse_conduit_events_from_html(
                soup, CONDUIT_URL, headers, download_images
            )
            print(f"🎸 Successfully scraped {len(events)} Conduit events")
            return events
        except requests.exceptions.HTTPError as e:
            last_err = e
            if e.response is not None and e.response.status_code == 403:
                print(
                    f"⚠️  Attempt {attempt + 1}: access forbidden, "
                    f"trying different user agent..."
                )
                continue
            print(f"❌ HTTP Error: {e}")
            break
        except Exception as e:
            last_err = e
            print(f"❌ Error on attempt {attempt + 1}: {e}")
    print(f"❌ All attempts failed ({last_err}), returning empty list")
    return []


def save_events(events, filename="conduit_events.json"):
    """Save events to JSON file."""
    with open(filename, "w") as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to {filename}")


if __name__ == "__main__":
    events = scrape_conduit_events(download_images=False)
    if events:
        save_events(events)
        print("\n📋 CONDUIT EVENTS SUMMARY:")
        print("=" * 30)
        for ev in events:
            print(f"🎵 {ev['title']}")
            print(f"   📅 {ev['date']} at {ev['time']}")
            print(f"   📍 {ev['venue']}")
            print(f"   💰 {ev['price']}")
            print(f"   🔞 {ev['age_restriction']}")
            print(f"   🖼️  {ev.get('flyer_url') or '(none)'}")
            print()
    else:
        print("❌ No events found")