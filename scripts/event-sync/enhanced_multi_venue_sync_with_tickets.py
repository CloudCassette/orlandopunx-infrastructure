#!/usr/bin/env python3
"""
🎸 Enhanced Multi-Venue Event Scraper with Ticket Links
========================================================
Scrapes events from Orlando venues and extracts ticket links
Includes: Will's Pub, Conduit FL with ticket purchasing info
"""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def extract_ticket_links(soup, event_url):
    """Extract ticket links from event pages"""
    ticket_links = []
    ticket_keywords = [
        'ticket', 'buy', 'purchase', 'eventbrite', 'ticketmaster', 
        'stubhub', 'seatgeek', 'bandcamp', 'venmo', 'paypal', 'rsvp'
    ]
    
    # Look for links containing ticket keywords
    for keyword in ticket_keywords:
        links = soup.find_all('a', href=re.compile(rf'{keyword}', re.I))
        for link in links:
            href = link.get('href')
            if href:
                # Make absolute URL
                abs_url = urljoin(event_url, href)
                link_text = link.get_text(strip=True)
                
                # Skip if it's just navigation or unrelated
                if any(skip in link_text.lower() for skip in ['home', 'about', 'contact', 'menu']):
                    continue
                
                ticket_links.append({
                    'url': abs_url,
                    'text': link_text or f'Tickets ({keyword})',
                    'type': keyword.lower()
                })
    
    # Look for common ticket platforms in any links
    ticket_domains = [
        'eventbrite.com', 'ticketmaster.com', 'stubhub.com', 
        'seatgeek.com', 'bandcamp.com', 'tix.com', 'ticketweb.com'
    ]
    
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href')
        if any(domain in href for domain in ticket_domains):
            abs_url = urljoin(event_url, href)
            link_text = link.get_text(strip=True)
            
            ticket_links.append({
                'url': abs_url,
                'text': link_text or 'Buy Tickets',
                'type': 'ticket_platform'
            })
    
    # Remove duplicates
    seen_urls = set()
    unique_tickets = []
    for ticket in ticket_links:
        if ticket['url'] not in seen_urls:
            seen_urls.add(ticket['url'])
            unique_tickets.append(ticket)
    
    return unique_tickets[:3]  # Limit to 3 ticket links max


def format_description_with_tickets(base_description, ticket_links, event_url):
    """Format event description with ticket information"""
    description = base_description
    
    if ticket_links:
        description += "\n\n🎫 Tickets:"
        for ticket in ticket_links:
            description += f"\n• {ticket['text']}: {ticket['url']}"
    
    # Always add the event URL for more info
    description += f"\n\n🔗 Event Info: {event_url}"
    
    return description


def scrape_willspub_events():
    """Scrape events from Will's Pub with ticket links"""
    print("🎸 Scraping Will's Pub events with ticket information...")

    url = "https://willspub.org"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        events = []

        # Look for Will's Pub event links
        event_links = soup.find_all("a", href=re.compile(r"/tm-event/"))
        print(f"📋 Found {len(event_links)} Will's Pub event links")

        # Remove duplicates by URL
        unique_events = {}
        for link in event_links:
            event_url = urljoin(url, link.get("href"))
            title = link.get_text(strip=True)

            if not title or len(title) < 3:
                continue
            if title.lower() in ["event", "events", "more info", "details"]:
                continue

            unique_events[event_url] = title

        print(f"📋 Found {len(unique_events)} unique Will's Pub events")

        for event_url, title in unique_events.items():
            try:
                print(f"   📝 Processing: {title}")

                # Get event details from individual page
                event_response = requests.get(event_url, headers=headers, timeout=30)
                event_response.raise_for_status()

                event_soup = BeautifulSoup(event_response.content, "html.parser")

                # Extract date and time
                date_element = event_soup.find("span", class_="tw-event-date")
                time_element = event_soup.find("span", class_="tw-event-time")

                date_text = date_element.get_text(strip=True) if date_element else None
                time_text = time_element.get_text(strip=True) if time_element else None

                # Parse date and time (simplified)
                event_date = "2025-08-21"  # default
                event_time = "19:00"  # default

                # Extract ticket links
                ticket_links = extract_ticket_links(event_soup, event_url)
                print(f"   🎫 Found {len(ticket_links)} ticket links")

                # Download flyer
                flyer_url, flyer_file = None, None
                og_image = event_soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    flyer_url = og_image.get("content")
                    if "willspub-logo" not in flyer_url.lower():
                        print(f"   🖼️  Found flyer: {flyer_url}")

                # Create enhanced description
                base_description = f"Live music at Will's Pub"
                enhanced_description = format_description_with_tickets(
                    base_description, ticket_links, event_url
                )

                event = {
                    "title": title,
                    "date": event_date,
                    "time": event_time,
                    "venue": "Will's Pub",
                    "venue_url": "https://willspub.org",
                    "url": event_url,
                    "description": enhanced_description,
                    "source": "willspub",
                    "flyer_url": flyer_url or "",
                    "flyer_file": flyer_file or "",
                    "ticket_links": ticket_links,
                    "raw_date": date_text,
                    "raw_time": time_text,
                }

                events.append(event)
                print(f"   ✅ {title} - {event_date} at {event_time}")

            except Exception as e:
                print(f"   ❌ Error processing {title}: {e}")
                continue

        print(f"🎸 Successfully scraped {len(events)} Will's Pub events with ticket info")
        return events

    except Exception as e:
        print(f"❌ Error scraping Will's Pub: {e}")
        return []


def scrape_conduit_events_with_tickets():
    """Scrape events from Conduit with ticket links"""
    print("🎸 Scraping Conduit events with ticket information...")

    url = "https://www.conduitfl.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        events = []

        # Look for event containers
        event_containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'event|show|concert'))
        
        if not event_containers:
            # Fallback: look for any containers with event-like content
            event_containers = soup.find_all('div')[:50]  # Check first 50 divs

        print(f"📋 Found {len(event_containers)} potential event containers")

        for container in event_containers[:20]:  # Limit to first 20
            try:
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                # Skip if it's not an event
                if not any(word in title.lower() for word in ['show', 'concert', 'music', 'band', 'live']):
                    continue

                # Look for date information
                event_date = "2025-08-21"  # default
                event_time = "19:00"  # default

                # Try to find ticket links in this event container
                ticket_links = extract_ticket_links(container, url)
                
                # Create enhanced description
                base_description = f"Live music at Conduit FL"
                enhanced_description = format_description_with_tickets(
                    base_description, ticket_links, url
                )

                event = {
                    "title": title,
                    "date": event_date,
                    "time": event_time,
                    "venue": "Conduit",
                    "venue_url": "https://www.conduitfl.com/",
                    "url": url,
                    "description": enhanced_description,
                    "source": "conduit",
                    "ticket_links": ticket_links,
                }

                events.append(event)
                print(f"   ✅ {title} - {len(ticket_links)} ticket links")

            except Exception as e:
                print(f"   ❌ Error processing event: {e}")
                continue

        print(f"🎸 Successfully scraped {len(events)} Conduit events with ticket info")
        return events[:10]  # Limit to 10 events

    except Exception as e:
        print(f"❌ Error scraping Conduit: {e}")
        return []


def main():
    """Test the enhanced scrapers"""
    print("🎯 TESTING ENHANCED SCRAPERS WITH TICKET LINKS")
    print("=" * 50)
    
    # Test Will's Pub
    print("\n🎸 Testing Will's Pub scraper...")
    willspub_events = scrape_willspub_events()
    
    # Test Conduit
    print("\n🎸 Testing Conduit scraper...")
    conduit_events = scrape_conduit_events_with_tickets()
    
    # Combine and show results
    all_events = willspub_events + conduit_events
    
    print(f"\n📊 RESULTS:")
    print(f"   🎸 Will's Pub: {len(willspub_events)} events")
    print(f"   🎸 Conduit: {len(conduit_events)} events")
    print(f"   📅 Total: {len(all_events)} events")
    
    # Show sample events with ticket info
    print(f"\n🎫 Sample events with ticket links:")
    for event in all_events[:3]:
        print(f"\n• {event['title']} ({event['venue']})")
        print(f"  Description: {event['description'][:200]}...")
        if event.get('ticket_links'):
            print(f"  Ticket links: {len(event['ticket_links'])}")
            for ticket in event['ticket_links']:
                print(f"    - {ticket['text']}: {ticket['url'][:50]}...")

    # Save enhanced events
    with open("enhanced_events_with_tickets.json", "w") as f:
        json.dump(all_events, f, indent=2)
    print(f"\n💾 Saved {len(all_events)} enhanced events to enhanced_events_with_tickets.json")

if __name__ == "__main__":
    main()
