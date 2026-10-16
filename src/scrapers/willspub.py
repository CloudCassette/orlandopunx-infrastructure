#!/usr/bin/env python3
"""
🎸 Will's Pub event scraper (TicketWeb plugin markup)
======================================================
Scrapes upcoming events from willspub.org. The homepage was rebuilt
on TicketWeb's plugin markup — one event per `div.tw-section`:

    <div class="tw-section">
      <div class="tw-image"><a href="/tm-event/...">
        <img class="event-img large" src="...flyer..."/></a></div>
      <div class="tw-name"> <a href="/tm-event/...">Title</a> </div>
      <div class="tw-date-time">
        <span class="tw-event-date-complete">
          <span class="tw-event-date">Fri Oct, 16 2026</span>
        </span>
        <span class="tw-event-door-time-complete">
          Doors: <span class="tw-event-door-time">06:00 PM</span>
        </span>
      </div>
      <div class="tw-venue-details"><span class="tw-venue-name">Will's Pub</span></div>
      <div class="tw-age-restriction">18 and up</div>
      <div class="event-description">...</div>
      <div class="tw-info-price-buy-tix">
        <span class="tw-price">$X</span>
        <a class="tw-buy-tix-btn" href="...ticketweb...">Buy Tickets</a>
      </div>
      ... google-calendar link with dates=YYYYMMDDTHHMMSS ...
    </div>

Selectors verified against the live page on 2026-10-16 (20 events).

Notes:
* https://willspub.org returns 403 to curl/requests; plain `http://`
  is served correctly. Use WILLSPUB_URL (http).
* Date text format is `%a %b, %d %Y` e.g. "Fri Oct, 16 2026". A robust
  fallback is the google-calendar link's `dates=YYYYMMDDTHHMMSS`.
* Only a "doors" time is structured on the page; a `Show:` time is
  sometimes embedded in the description text and is preferred when
  present (gcal uses the doors time). Falls back to doors, then gcal.
* Titles join bands with U+2028 line separators; normalised here.

Standalone usage:
    python src/scrapers/willspub.py
"""

import json
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# https 403s to plain requests (nginx); http works.
# NOTE (verified 2026-10-16): willspub.org's nginx 403s most "modern"
# Chrome/Firefox UA strings (anything carrying a Chrome/ or Gecko/ token)
# while allowing bare WebKit and Safari-style UAs. The single UA below
# works; a small fallback list is used in case of a 403 anyway.
WILLSPUB_URL = "http://willspub.org/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

HEADERS = {
    "User-Agent": USER_AGENTS[0],
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
}

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_DATE_RE = re.compile(
    r"([A-Za-z]{3,})\.?,?\s*(\d{1,2})\.?,?\s+(\d{4})"
)
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*([AaPp][Mm])")
_SHOW_TIME_RE = re.compile(r"Show:\s*(\d{1,2}):(\d{2})\s*([AaPp][Mm])")
_GCAL_RE = re.compile(r"dates=(\d{8})T(\d{6})")

_SKIP_PHRASES = [
    "More Info",
    "Buy Tickets",
    "Click here",
    "View Details",
    "Learn More",
    "Read More",
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def clean_event_title(title):
    """Clean up an event title (normalise U+2028 separators, whitespace)."""
    if not title:
        return ""
    # Band lists use U+2028 line separators; the source already puts a
    # comma before them ("Skies,\u2028No One Road"), so collapse both.
    title = title.replace("\u2028", " ").replace("\u2029", " ")
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s*,\s*,", ",", title)
    return title.strip(" ,")


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


def parse_willspub_date(date_text):
    """Parse 'Fri Oct, 16 2026' -> 'YYYY-MM-DD' (or None)."""
    if not date_text:
        return None
    m = _DATE_RE.search(date_text)
    if not m:
        return None
    month_name, day, year = m.group(1), int(m.group(2)), int(m.group(3))
    month = _MONTHS.get(month_name.lower()[:3])
    if not month:
        return None
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_event_time(description, door_text, gcal_time=None):
    """Best-effort event start time -> 'HH:MM'.

    Preference: `Show:` in the description (true concert start), then the
    structured doors time, then the gcal link (which mirrors doors), then
    a default of 20:00 (matching the historical sync behaviour).
    """
    show = _SHOW_TIME_RE.search(description or "")
    if show:
        return _to_24h(show.group(1), show.group(2), show.group(3))
    door = _TIME_RE.search(door_text or "")
    if door:
        return _to_24h(door.group(1), door.group(2), door.group(3))
    if gcal_time:
        return f"{int(gcal_time[:2]):02d}:{gcal_time[2:4]}"
    return "20:00"


def extract_event_flyer(section, base_url):
    """Flyer URL from the `.tw-image img` inside a section (or '')."""
    img = section.find("img", class_="event-img")
    if img and img.get("src"):
        return urljoin(base_url, img["src"].strip())
    return ""


# --------------------------------------------------------------------------
# parsing (DOM-in, dicts-out — testable without network)
# --------------------------------------------------------------------------

def parse_willspub_events_from_html(soup, base_url=None):
    """Parse Will's Pub events from a BeautifulSoup of the homepage.

    Returns a list of dicts (canonical shape):
        title, venue, date, time, description, url, flyer_url,
        price, age_restriction
    Events without a parseable concrete date are logged and skipped.
    """
    base_url = base_url or WILLSPUB_URL
    events = []
    sections = soup.find_all(class_="tw-section")
    if not sections:
        print("   ⚠️ No .tw-section event blocks found on Will's Pub page")
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
                print(f"   ⏭️ Skipped (empty/boilerplate title): {raw_title!r}")
                continue

            href = a.get("href") if a is not None else None
            url = urljoin(base_url, href) if href else base_url

            # --- concrete date: tw-event-date text, gcal fallback ---
            date_el = section.find(class_="tw-event-date")
            date_text = date_el.get_text(strip=True) if date_el else ""
            event_date = parse_willspub_date(date_text)

            gcal = section.find(
                "a", href=lambda h: h and "google.com/calendar" in h
            )
            gcal_match = _GCAL_RE.search(gcal.get("href", "")) if gcal else None
            if not event_date and gcal_match:
                try:
                    event_date = datetime.strptime(
                        gcal_match.group(1), "%Y%m%d"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    event_date = None
            if not event_date:
                print(
                    f"   ⏭️ SKIPPED (no parseable date): {title[:60]!r} — "
                    f"date text {date_text!r}"
                )
                continue

            # --- time ---
            door_el = section.find(class_="tw-event-door-time")
            door_text = door_el.get_text(strip=True) if door_el else ""
            desc_el = section.find(class_="event-description")
            description = (
                desc_el.get_text(" ", strip=True) if desc_el else ""
            )
            event_time = parse_event_time(
                description, door_text,
                gcal_match.group(2) if gcal_match else None,
            )

            # --- extras ---
            price_el = section.find(class_="tw-price")
            price = price_el.get_text(strip=True) if price_el else ""
            age_el = section.find(class_="tw-age-restriction")
            age = age_el.get_text(strip=True) if age_el else ""

            events.append({
                "title": title,
                "venue": "Will's Pub",
                "date": event_date,
                "time": event_time,
                "description": description,
                "url": url,
                "flyer_url": extract_event_flyer(section, base_url),
                "price": price,
                "age_restriction": age,
                "source": "willspub",
            })
            print(f"   ✅ {title} - {event_date} at {event_time}")
        except Exception as e:
            print(f"   ❌ Error parsing Will's Pub event: {e}")
            continue
    return events


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def scrape_willspub_events(download_images=False):
    """Scrape events from willspub.org.

    `download_images` is accepted for signature compatibility with the
    other scrapers; flyers are surfaced as URLs (the page already embeds
    them), so nothing is downloaded here.
    """
    print("🎸 Scraping Will's Pub events (TicketWeb markup)...")
    last_err = None
    for attempt, user_agent in enumerate(USER_AGENTS):
        headers = dict(HEADERS)
        headers["User-Agent"] = user_agent
        try:
            response = requests.get(WILLSPUB_URL, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            events = parse_willspub_events_from_html(soup, WILLSPUB_URL)
            print(f"🎸 Successfully scraped {len(events)} Will's Pub events")
            return events
        except requests.exceptions.HTTPError as e:
            last_err = e
            status = (
                e.response.status_code
                if e.response is not None else None
            )
            print(
                f"   ⚠️ Attempt {attempt + 1}: HTTP {status}, "
                f"trying next user agent..."
            )
            continue
        except Exception as e:
            last_err = e
            print(f"   ❌ Error on attempt {attempt + 1}: {e}")
            continue
    print(f"❌ Error scraping Will's Pub: {last_err}")
    return []


if __name__ == "__main__":
    events = scrape_willspub_events()
    with open("willspub_events_enhanced.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"💾 Saved {len(events)} events to willspub_events_enhanced.json")
    print("\n🎯 RESULTS:")
    for ev in events[:10]:
        print(
            f"   • {ev['title']}\n"
            f"     {ev['date']} @ {ev['time']} · {ev['venue']}\n"
            f"     flyer: {ev.get('flyer_url') or '(none)'}\n"
            f"     {ev['url']}"
        )