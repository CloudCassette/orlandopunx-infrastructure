#!/usr/bin/env python3
"""
🎨 The Falcon event scraper (Eventbrite organizer page)
=========================================================
Scrapes upcoming events from The Falcon Bar & Gallery's Eventbrite
organizer page: https://www.eventbrite.com/o/the-falcon-37975560053

The Falcon has no standalone venue site — its shows (live music, DJs,
burlesque, art nights, weekly recurring events) are listed on Eventbrite.
The organizer page is server-rendered (Next.js); each upcoming event is a
"vertical event card" with:

    <div class="...VerticalEventCard...">
      <a data-event-id="1717349411319" data-event-location="Orlando, FL"
         data-event-paid-status="free" href="/e/...-tickets-1717349411319">
        <img src="https://img.evbuc.com/..."/>
      </a>
      <section>
        <h3>Open Mic @TheFalconBar</h3>
        <p>Today • 8:30 PM and 9+ more</p>        <- date line
        <p>The Falcon Bar & Gallery</p>
        <p>Free</p>
      </section>
    </div>

The date line is relative ("Today"/"Tomorrow"/weekday) for recurring
series and "Mon, Nov 16" for dated ones, always the NEXT occurrence —
which is what a calendar wants. Times are venue-local
(America/New_York). There are no JSON-LD dates we can trust: the detail
page's startDate is the series' ORIGINAL first occurrence, not the next.

Selectors verified against the live page on 2026-11-10 (12 events).

Standalone usage:
    python src/scrapers/falcon.py
"""

import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

FALCON_ORGANIZER_URL = "https://www.eventbrite.com/o/the-falcon-37975560053"
EVENTBRITE_BASE = "https://www.eventbrite.com"

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

TZ = ZoneInfo("America/New_York")

_WEEKDAYS = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}
_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
           "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

# "Today • 8:30 PM and 9+ more" / "Mon, Nov 16 •  5:00 PM  and 9+ more"
_DATE_LINE_RE = re.compile(
    r"^\s*(.+?)\s*•\s*(\d{1,2}):(\d{2})\s*(AM|PM)", re.I
)
# strip the recurring-series tail from the day part
_MORE_RE = re.compile(r"\s+and\s+\d+\+?\s+more\s*$", re.I)
# dated: "Mon, Nov 16"
_MONTH_DAY_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+([A-Za-z]{3,})\.?\s+(\d{1,2})$", re.I)
# bare weekday: "Sunday"
_BARE_WEEKDAY_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day)?$", re.I)


def resolve_next_date(day_part, hour, minute, now=None):
    """Resolve a card's relative day text + time to (date, 'HH:MM') or None.

    Handles:
      * "Today" / "Tomorrow"
      * bare weekday ("Sunday") — the next such weekday (rolls to +7 when
        today's occurrence already started)
      * dated weekday ("Mon, Nov 16") — year inferred like the Conduit
        scraper: nearest candidate (current/next year) whose weekday
        matches, never more than 30 days in the past.
    """
    now = now or datetime.now(TZ)
    today = now.date()
    day_part = _MORE_RE.sub("", day_part or "").strip()

    def _hm(dt):
        return dt.strftime("%H:%M")

    # --- Today / Tomorrow ---
    if day_part.lower() in ("today", "tomorrow"):
        offset = 1 if day_part.lower() == "tomorrow" else 0
        base = today + timedelta(days=offset)
        dt = datetime(base.year, base.month, base.day, hour, minute, tzinfo=TZ)
        if dt < now:
            return None  # occurrence already started
        return base, _hm(dt)

    # --- dated "Mon, Nov 16" ---
    m = _MONTH_DAY_RE.match(day_part)
    if m:
        wanted = _WEEKDAYS[m.group(1).lower()[:3]]
        month = _MONTHS.get(m.group(2).lower()[:3])
        day = int(m.group(3))
        if not month:
            return None
        candidates = [now.year, now.year + 1]
        if now.month == 1:  # January listings can be last December's page
            candidates.insert(0, now.year - 1)
        best = None
        for year in candidates:
            try:
                dt = datetime(year, month, day, hour, minute, tzinfo=TZ)
            except ValueError:
                continue
            age = (now - dt).days
            if age > 30:  # too far in the past -> not an upcoming listing
                continue
            if dt.weekday() != wanted:
                continue
            if best is None or age < best[0]:
                best = (age, dt)
        if best is None:
            return None
        return best[1].date(), _hm(best[1])

    # --- bare weekday "Sunday" ---
    m = _BARE_WEEKDAY_RE.match(day_part)
    if not m:
        return None
    wanted = _WEEKDAYS[m.group(1).lower()[:3]]
    offset = (wanted - today.weekday()) % 7
    dt = datetime(today.year, today.month, today.day, hour, minute, tzinfo=TZ)
    dt += timedelta(days=offset)
    if dt < now:
        dt += timedelta(days=7)  # today's occurrence passed -> next week
    return dt.date(), _hm(dt)


def extract_event_card(card):
    """Pull one event dict from a vertical event card div (or None)."""
    link = card.find("a", attrs={"data-event-id": True})
    if link is None:
        return None
    event_id = link["data-event-id"]

    title_el = card.find("h3")
    title = (title_el.get_text(strip=True) if title_el else "") or ""
    if not title:
        aria = link.get("aria-label") or ""
        title = re.sub(r"^View\s+", "", aria, flags=re.I).strip()
    if not title or len(title) < 3:
        return None

    href = link.get("href") or ""
    event_url = urljoin(EVENTBRITE_BASE, href)

    img = card.find("img")
    image_url = (img.get("src") or "").strip() if img else ""

    lines = [t for t in card.stripped_strings]
    date_line = next((t for t in lines if "•" in t), "")
    m = _DATE_LINE_RE.search(date_line)
    if not m:
        return None
    hour, minute, period = int(m.group(2)), int(m.group(3)), m.group(4)
    resolved = resolve_next_date(m.group(1), hour, minute)
    if resolved is None:
        return None
    event_date, event_time = resolved

    # The venue line is the card's "The Falcon Bar & Gallery" line —
    # skip the title line, which often contains "Falcon" too.
    venue = next(
        (t for t in lines[1:] if "Falcon" in t and "•" not in t and t != title),
        "The Falcon",
    )
    price = next((t for t in lines if re.match(r"^\$|^Free", t, re.I)), "")

    return {
        "title": title,
        "venue": venue,
        "date": event_date.strftime("%Y-%m-%d"),
        "time": event_time,
        "description": "",
        "url": event_url,
        "flyer_url": image_url,
        "price": price,
        "age_restriction": "",
        # The Eventbrite event page IS the ticket page.
        "ticket_url": event_url,
        "source": "falcon",
        "_event_id": event_id,
    }


def parse_falcon_events_from_html(html):
    """Parse events from a BeautifulSoup-friendly HTML string.

    Returns a list of dicts (canonical scraper shape, minus the private
    ``_event_id`` key), deduplicated by Eventbrite event id.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    events = []
    cards = soup.find_all(
        "div", class_=lambda c: bool(c and "VerticalEventCard" in c)
    )
    for card in cards:
        try:
            ev = extract_event_card(card)
        except Exception as e:
            print(f"   ❌ Error parsing Falcon card: {e}")
            continue
        if ev is None:
            continue
        eid = ev.pop("_event_id", None)
        if eid in seen:
            continue
        seen.add(eid)
        events.append(ev)
    if not events:
        print("   ⚠️ No Falcon event cards found (page structure changed?)")
    return events


def scrape_falcon_events(download_images=False):
    """Scrape events from The Falcon's Eventbrite organizer page.

    `download_images` is accepted for signature compatibility; flyers are
    surfaced as URLs (Eventbrite's img.evbuc.com CDN), nothing is
    downloaded here.
    """
    print("🎨 Scraping The Falcon events (Eventbrite organizer page)...")
    last_err = None
    for attempt, user_agent in enumerate(USER_AGENTS):
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            response = requests.get(FALCON_ORGANIZER_URL, headers=headers, timeout=30)
            response.raise_for_status()
            events = parse_falcon_events_from_html(response.text)
            print(f"🎨 Successfully scraped {len(events)} Falcon events")
            return events
        except requests.exceptions.HTTPError as e:
            last_err = e
            status = e.response.status_code if e.response is not None else None
            print(f"   ⚠️ Attempt {attempt + 1}: HTTP {status}, retrying...")
            continue
        except Exception as e:
            last_err = e
            print(f"   ❌ Error on attempt {attempt + 1}: {e}")
            continue
    print(f"❌ Error scraping The Falcon: {last_err}")
    return []


if __name__ == "__main__":
    events = scrape_falcon_events()
    with open("falcon_events.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to falcon_events.json")
    for ev in events:
        print(
            f"   • {ev['title']}\n"
            f"     {ev['date']} @ {ev['time']} · {ev['venue']} · {ev['price']}\n"
            f"     {ev['url']}"
        )
