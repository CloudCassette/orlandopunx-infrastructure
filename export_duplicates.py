#!/usr/bin/env python3

import re
from collections import defaultdict

# Load events from saved HTML
events = []
with open("admin_after_click.html", "r") as f:
    html_content = f.read()

pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
matches = re.findall(pattern, html_content)

for match in matches:
    event_id, title_var, slug = match
    events.append({"id": int(event_id), "slug": slug})

# Group by base slug
base_slug_groups = defaultdict(list)
for event in events:
    base_slug = re.sub(r"-\d+$", "", event["slug"])
    base_slug_groups[base_slug].append(event)

# Find duplicates
duplicates_to_delete = []
kept_originals = []

for base_slug, event_list in base_slug_groups.items():
    if len(event_list) > 1:
        event_list.sort(key=lambda x: x["id"])
        kept_originals.append(event_list[0])
        duplicates_to_delete.extend(event_list[1:])

# Sort duplicates by ID
duplicates_to_delete.sort(key=lambda x: x["id"])

# Export to file
with open("duplicate_event_ids.txt", "w") as f:
    f.write("DUPLICATE EVENT IDs TO DELETE\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Total duplicates: {len(duplicates_to_delete)}\n")
    f.write(f"Events to keep: {len(kept_originals)}\n\n")
    f.write("IDs to delete (comma-separated for easy copy/paste):\n")
    f.write(",".join(str(d["id"]) for d in duplicates_to_delete))
    f.write("\n\nDetailed list:\n")
    for i, dup in enumerate(duplicates_to_delete, 1):
        f.write(f"{i}. ID: {dup['id']} - {dup['slug']}\n")

print(
    f"✅ Exported {len(duplicates_to_delete)} duplicate IDs to 'duplicate_event_ids.txt'"
)
print(
    f"\n📋 First 10 duplicate IDs: {','.join(str(d['id']) for d in duplicates_to_delete[:10])}"
)
