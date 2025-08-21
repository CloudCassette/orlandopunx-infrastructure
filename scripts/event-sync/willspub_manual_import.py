#!/usr/bin/env python3
"""
Will's Pub Event Extractor - For Manual Import
Creates formatted text files for easy copy/paste into Gancio
"""

import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def scrape_and_format_events(limit=10):
    """Scrape events and format for manual import"""
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )

    try:
        print(f"📥 Scraping events from Will's Pub...")
        response = session.get("https://willspub.org", timeout=30)
        response.raise_for_status()

        content = response.text

        # Extract events
        events = []
        lines = content.split("\n")

        for line in lines:
            if "EventData.events.push" in line and '"type" : "event"' in line:
                try:
                    display_match = re.search(r'"display" : "([^"]+)"', line)
                    url_match = re.search(r'"url" : "([^"]+)"', line)

                    if all([display_match, url_match]):
                        display = (
                            display_match.group(1)
                            .replace("&amp;", "&")
                            .replace("&#039;", "'")
                        )

                        # Parse title
                        date_match = re.search(r"(\d{2}/\d{2})$", display)
                        if date_match:
                            title = display[:-6].strip()
                        else:
                            title = display

                        events.append({"title": title, "url": url_match.group(1)})

                        if limit and len(events) >= limit:
                            break

                except Exception:
                    continue

        print(f"✅ Found {len(events)} events")

        # Get details for each event
        formatted_events = []
        for i, event in enumerate(events, 1):
            print(f"📋 [{i}/{len(events)}] Processing: {event['title']}")

            try:
                event_resp = session.get(event["url"], timeout=15)
                soup = BeautifulSoup(event_resp.content, "html.parser")

                details = {
                    "title": event["title"],
                    "url": event["url"],
                    "venue": "Will's Pub",
                }

                # Extract date
                date_elem = soup.find("span", class_="tw-event-date")
                if date_elem:
                    date_str = date_elem.text.strip()
                    details["date_raw"] = date_str
                    details["date_formatted"] = parse_date(date_str)

                # Extract time
                time_elem = soup.find("span", class_="tw-event-door-time")
                if time_elem:
                    time_str = time_elem.text.strip()
                    details["time_raw"] = time_str
                    details["time_formatted"] = parse_time(time_str)
                else:
                    details["time_formatted"] = "19:00"

                # Extract price
                price_elem = soup.find("span", class_="tw-price")
                if price_elem:
                    details["price"] = price_elem.text.strip()

                # Extract description
                desc_elem = soup.find("div", class_="event-description")
                if desc_elem:
                    details["description"] = desc_elem.get_text().strip()
                else:
                    details["description"] = f"Live music event at {details['venue']}"

                formatted_events.append(details)
                time.sleep(0.5)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        return formatted_events

    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return []


def parse_date(date_str):
    """Parse date string to readable format"""
    try:
        date_str = re.sub(r"\s+", " ", date_str.strip())

        formats = [
            "%b %d, %Y",  # Aug 10, 2025
            "%a %b, %d %Y",  # Sun Aug, 10 2025
            "%a %b %d, %Y",  # Sun Aug 10, 2025
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return {
                    "iso": parsed_date.strftime("%Y-%m-%d"),
                    "readable": parsed_date.strftime("%B %d, %Y"),
                    "day": parsed_date.strftime("%A"),
                }
            except ValueError:
                continue

        return None
    except Exception:
        return None


def parse_time(time_str):
    """Parse time string"""
    try:
        time_match = re.search(r"(\d{1,2}):(\d{2})\s*([AP]M)", time_str, re.I)
        if time_match:
            hour, minute, ampm = time_match.groups()
            hour = int(hour)
            minute = int(minute)

            if ampm.upper() == "PM" and hour != 12:
                hour += 12
            elif ampm.upper() == "AM" and hour == 12:
                hour = 0

            return {
                "24h": f"{hour:02d}:{minute:02d}",
                "12h": f"{int(hour) if hour <= 12 else hour-12}:{minute:02d} {ampm.upper()}",
            }

        return {"24h": "19:00", "12h": "7:00 PM"}
    except Exception:
        return {"24h": "19:00", "12h": "7:00 PM"}


def generate_import_files(events):
    """Generate files for import"""

    # 1. Generate CSV for spreadsheet import
    csv_content = "Title,Date,Time,Venue,Price,Description,URL\n"

    # 2. Generate formatted text for manual copy/paste
    text_content = "WILL'S PUB EVENTS FOR GANCIO IMPORT\n"
    text_content += "=" * 50 + "\n"
    text_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text_content += f"Total Events: {len(events)}\n\n"

    # 3. Generate JSON for potential API use later
    json_events = []

    for i, event in enumerate(events, 1):
        title = event.get("title", "Unknown Event")
        date_info = event.get("date_formatted")
        time_info = event.get("time_formatted")
        venue = event.get("venue", "Will's Pub")
        price = event.get("price", "Free")
        description = event.get("description", "")
        url = event.get("url", "")

        # CSV line
        csv_line = f'"{title}","{date_info.get("iso", "") if date_info else ""}","{time_info.get("24h", "") if time_info else ""}","{venue}","{price}","{description.replace(chr(34), chr(39))}","{url}"\n'
        csv_content += csv_line

        # Text format
        text_content += f"EVENT #{i}: {title}\n"
        text_content += f"{'=' * (10 + len(str(i)) + len(title))}\n"
        if date_info:
            text_content += f"📅 Date: {date_info['readable']} ({date_info['day']})\n"
            text_content += f"    ISO Format: {date_info['iso']}\n"
        if time_info:
            text_content += f"🕐 Time: {time_info['12h']} ({time_info['24h']})\n"
        text_content += f"📍 Venue: {venue}\n"
        if price:
            text_content += f"💰 Price: {price}\n"
        text_content += f"🔗 URL: {url}\n"
        text_content += f"📝 Description:\n{description}\n"
        text_content += "\n" + "-" * 50 + "\n\n"

        # JSON format
        json_event = {
            "title": title,
            "date": date_info["iso"] if date_info else None,
            "time": time_info["24h"] if time_info else None,
            "venue": venue,
            "price": price,
            "description": description,
            "source_url": url,
        }
        json_events.append(json_event)

    # Write files
    with open("willspub_events.csv", "w") as f:
        f.write(csv_content)

    with open("willspub_events.txt", "w") as f:
        f.write(text_content)

    with open("willspub_events.json", "w") as f:
        json.dump(json_events, f, indent=2)

    print(f"\n✨ Generated import files:")
    print(f"   📄 willspub_events.txt - Formatted for manual copy/paste")
    print(f"   📊 willspub_events.csv - For spreadsheet import")
    print(f"   📋 willspub_events.json - For future API use")


def main():
    print("📋 Will's Pub Event Extractor for Manual Import")
    print("=" * 50)

    limit = input("How many events to process? (default: 10): ").strip()
    try:
        limit = int(limit) if limit else 10
    except ValueError:
        limit = 10

    events = scrape_and_format_events(limit=limit)

    if not events:
        print("❌ No events found")
        return

    print(f"\n✅ Successfully processed {len(events)} events")
    generate_import_files(events)

    print(f"\n🎯 Next Steps:")
    print(f"   1. Open willspub_events.txt to see all event details")
    print(f"   2. Go to your Gancio admin panel")
    print(f"   3. Manually create events using the formatted information")
    print(f"   4. Copy/paste titles, dates, descriptions as needed")


if __name__ == "__main__":
    main()
