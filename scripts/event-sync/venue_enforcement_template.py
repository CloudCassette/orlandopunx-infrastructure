
# Enhanced Venue Assignment Template for Sync Scripts

def ensure_venue_assignment(event_data: Dict) -> Dict:
    """Ensure every event has a valid venue assignment"""
    
    # 1. Extract venue information from multiple sources
    venue_sources = [
        event_data.get('venue'),
        event_data.get('location'), 
        event_data.get('place', {}).get('name') if isinstance(event_data.get('place'), dict) else None,
        extract_venue_from_title(event_data.get('title', '')),
        extract_venue_from_description(event_data.get('description', ''))
    ]
    
    # 2. Find the first valid venue
    venue_name = None
    for source in venue_sources:
        if source and source.strip():
            venue_name = source.strip()
            break
    
    # 3. Map venue name to venue info
    venue_validator = VenueValidator()
    venue_info = venue_validator.get_venue_info(venue_name, event_data)
    
    # 4. Ensure all venue fields are set
    event_data['venue'] = venue_info['name']
    event_data['place_id'] = venue_info['id']
    event_data['place'] = {
        'id': venue_info['id'],
        'name': venue_info['name'],
        'address': venue_info.get('address', '')
    }
    
    # 5. Validation check
    if not event_data.get('place_id') or event_data.get('place_id') == 0:
        print(f"⚠️ WARNING: Event still missing venue after assignment: {event_data.get('title', 'Unknown')}")
        # Force default venue as last resort
        event_data['place_id'] = 1  # Will's Pub
    
    return event_data

def extract_venue_from_title(title: str) -> Optional[str]:
    """Extract venue from event title"""
    venue_patterns = {
        r'@\s*([^,
]+)': 1,  # "Event @ Venue"
        r'at\s+([^,
]+)': 1,  # "Event at Venue"
        r'(conduit)': 1,   # Conduit mentions
        r'(will'?s\s*pub)': 1,  # Will's Pub mentions
    }
    
    for pattern, _ in venue_patterns.items():
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

# Example usage in sync script:
def create_event_in_gancio(raw_event_data):
    # 1. Process and clean event data
    processed_event = process_event_data(raw_event_data)
    
    # 2. CRITICAL: Ensure venue assignment
    processed_event = ensure_venue_assignment(processed_event)
    
    # 3. Validate before sending to API
    if not processed_event.get('place_id'):
        raise ValueError(f"Event missing venue assignment: {processed_event.get('title')}")
    
    # 4. Create in Gancio
    gancio_payload = {
        'title': processed_event['title'],
        'description': processed_event.get('description', ''),
        'start_datetime': processed_event['start_datetime'],
        'place_id': processed_event['place_id'],  # MUST be present
        # ... other fields
    }
    
    response = session.post(f"{gancio_url}/api/event", json=gancio_payload)
    return response
