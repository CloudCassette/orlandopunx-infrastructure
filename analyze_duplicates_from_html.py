#!/usr/bin/env python3

import re
from collections import defaultdict


def parse_events_from_html(filename):
    """Parse events directly from the saved HTML file"""
    with open(filename, "r") as f:
        content = f.read()

    events = []

    # Find all events in the unconfirmedEvents array
    # Pattern: {id:NUMBER,title:VARIABLE,slug:"SLUG",...}
    pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"'

    matches = re.findall(pattern, content)

    for match in matches:
        event_id, title_var, slug = match
        events.append({"id": int(event_id), "title_var": title_var, "slug": slug})

    return events


def analyze_duplicates(events):
    """Analyze events for duplicates based on slug patterns"""

    # Group by base slug (remove trailing -NUMBER)
    base_slug_groups = defaultdict(list)

    for event in events:
        base_slug = re.sub(r"-\d+$", "", event["slug"])
        base_slug_groups[base_slug].append(event)

    # Find duplicates
    duplicates = {}
    total_duplicate_count = 0

    for base_slug, event_list in base_slug_groups.items():
        if len(event_list) > 1:
            duplicates[base_slug] = event_list
            # Count all but the first one as duplicates
            total_duplicate_count += len(event_list) - 1

    return duplicates, total_duplicate_count


def main():
    filename = "admin_after_click.html"

    print("Parsing events from saved HTML file...")
    events = parse_events_from_html(filename)
    print(f"Found {len(events)} total events")

    print("\nAnalyzing duplicates...")
    duplicates, total_duplicate_count = analyze_duplicates(events)

    print(f"\nDuplicate Analysis Results:")
    print(f"Number of unique event types with duplicates: {len(duplicates)}")
    print(f"Total duplicate events that could be removed: {total_duplicate_count}")
    print(
        f"Events that would remain after cleanup: {len(events) - total_duplicate_count}"
    )

    print(f"\nDetailed breakdown:")

    # Sort by number of duplicates descending
    sorted_duplicates = sorted(
        duplicates.items(), key=lambda x: len(x[1]), reverse=True
    )

    for base_slug, duplicate_list in sorted_duplicates:
        duplicate_count = len(duplicate_list) - 1  # Don't count the original
        print(
            f"\n'{base_slug}': {len(duplicate_list)} total ({duplicate_count} duplicates)"
        )

        # Show ID ranges for reference
        ids = [event["id"] for event in duplicate_list]
        ids.sort()
        print(f"  IDs: {ids[0]} to {ids[-1]}")

        # Show first few slugs as examples
        sample_slugs = [event["slug"] for event in duplicate_list[:3]]
        if len(duplicate_list) > 3:
            sample_slugs.append(f"... and {len(duplicate_list)-3} more")
        print(f"  Examples: {', '.join(sample_slugs)}")


if __name__ == "__main__":
    main()
