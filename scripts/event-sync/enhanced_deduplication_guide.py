# Enhanced Deduplication Logic for Sync Scripts
# Add this to your sync scripts:


def enhanced_duplicate_check(existing_events, new_event_title):
    """Enhanced duplicate checking with fuzzy matching"""
    import hashlib

    title = new_event_title.strip()

    # Exact match check
    existing_titles = {event.get("title", "").strip() for event in existing_events}
    if title in existing_titles:
        return True, "Exact title match"

    # Normalized fuzzy check
    normalized_new = " ".join(title.lower().split())

    for existing_event in existing_events:
        existing_title = existing_event.get("title", "").strip()
        normalized_existing = " ".join(existing_title.lower().split())

        if normalized_new == normalized_existing:
            return True, f"Fuzzy match with: {existing_title}"

    return False, None


# Usage in sync scripts:
"""
existing_gancio_events = get_gancio_events()
for new_event in scraped_events:
    is_duplicate, reason = enhanced_duplicate_check(existing_gancio_events, new_event['title'])
    if is_duplicate:
        print(f"⚠️ Skipping duplicate: {new_event['title']} ({reason})")
        continue
    # Create event...
"""
