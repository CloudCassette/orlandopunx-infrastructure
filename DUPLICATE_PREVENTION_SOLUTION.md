# Orlando Punx Events - Duplicate Prevention Solution

## Problem Summary

The current sync system was experiencing issues with:
1. **Duplicate events flooding the approval queue** - Same events being submitted multiple times
2. **Excessive sync frequency** - Running 3 times daily even when no new events exist
3. **Poor event fetching strategy** - Always fetching all events instead of just new/changed ones
4. **Weak deduplication logic** - Only using simple title matching

## Solution Overview

This solution implements several key improvements to address the root causes:

### 1. Enhanced Deduplication System

**File:** `src/sync/improved_sync.py`

**Key Features:**
- **Composite Event Signatures:** Events are identified using `title|venue|date` combinations
- **Content Hashing:** SHA-256 hashes prevent exact duplicate submissions
- **Persistent State Tracking:** Events processed once are never resubmitted
- **Fuzzy Matching:** Similar titles on same date/venue are caught as duplicates
- **Multi-level Checks:**
  1. Check persistent state first
  2. Check against existing Gancio events
  3. Perform fuzzy matching as fallback

### 2. Intelligent Scheduling

**Key Changes:**
- **Reduced frequency:** From 3x daily to 2x daily (9am, 9pm EST)
- **Smart interval checking:** Won't run again within 12 hours
- **State persistence:** Remembers what events have been processed
- **Manual override:** Can force sync when needed

### 3. Better Workflow Management

**File:** `.github/workflows/improved-sync.yml`

**Improvements:**
- **Health checks** before attempting sync
- **Intelligent scheduling** built into workflow
- **Better error handling** and reporting
- **State file management** for persistence

### 4. Duplicate Cleanup Tool

**File:** `src/sync/cleanup_duplicates.py`

**Purpose:** Clean up existing duplicates in the approval queue

**Features:**
- **Safe analysis mode:** Preview what would be removed
- **Confirmation prompts:** Prevent accidental deletions
- **Keeps oldest events:** Preserves the original submission
- **Detailed reporting:** Shows exactly what will be cleaned up

## Implementation Steps

### Step 1: Clean Up Existing Duplicates

```bash
# First, analyze the current duplicate situation
cd /home/cloudcassette/orlandopunx-infrastructure/src/sync
python3 cleanup_duplicates.py --analyze

# Preview what would be cleaned up
python3 cleanup_duplicates.py --preview

# Actually clean up duplicates (requires confirmation)
python3 cleanup_duplicates.py --cleanup
```

### Step 2: Deploy Improved Sync System

The improved sync system is ready to deploy. It includes:

1. **Persistent state management** - Won't reprocess the same events
2. **Better deduplication** - Multiple strategies to catch duplicates
3. **Intelligent scheduling** - Only runs when likely to find new events

### Step 3: Update Workflow

Replace the current workflow with the improved version:

```bash
# The new workflow is already created at:
# .github/workflows/improved-sync.yml

# It includes:
# - Reduced frequency (2x daily instead of 3x)
# - Smart scheduling checks
# - Better error handling
```

## Key Improvements Explained

### 1. Event Hashing Strategy

**Old System:** Simple title comparison
```python
if new_title.lower() == existing_title.lower():
    # Skip as duplicate
```

**New System:** Multi-factor composite signatures
```python
def create_event_hash(event):
    content = {
        'title': normalize_text(event.get('title', '')),
        'venue': normalize_text(event.get('venue', '')),
        'date': normalize_date(event.get('start_datetime')),
        'description': normalize_text(event.get('description', ''))[:200]
    }
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
```

### 2. Persistent State Tracking

**Problem:** Events were being reprocessed every sync run

**Solution:** Pickle-based state persistence
```python
class PersistentStateManager:
    def __init__(self):
        self.processed_events = {}  # event_hash -> EventState
        self.load_state()  # Load from disk

    def is_event_processed(self, event_hash):
        return event_hash in self.processed_events
```

### 3. Intelligent Scheduling

**Problem:** Syncing 3x daily regardless of activity

**Solution:** Smart interval checking
```python
def should_run_sync():
    # Only run if it's been more than 12 hours
    hours_since_last = (datetime.now() - last_run).total_seconds() / 3600
    return hours_since_last >= 12
```

## Configuration

### Environment Variables

The system uses the same environment variables as the current system:
- `GANCIO_EMAIL` - Gancio admin email
- `GANCIO_PASSWORD` - Gancio admin password
- `GANCIO_BASE_URL` - Gancio base URL (default: http://localhost:13120)

### State File Location

Event processing state is stored in:
`src/sync/event_state.pkl`

This file is automatically managed and shouldn't be edited manually.

## Monitoring and Troubleshooting

### Check Duplicate Status
```bash
python3 src/sync/cleanup_duplicates.py --analyze
```

### Check Last Sync Time
```bash
cat /tmp/orlandopunx_last_sync
```

### Force Sync (Manual)
```bash
python3 src/sync/improved_sync.py
```

### View State File Contents
```python
import pickle
with open('src/sync/event_state.pkl', 'rb') as f:
    state = pickle.load(f)
    print(f"Tracked events: {len(state)}")
```

## Expected Results

After implementing this solution:

1. **No more duplicate events** in the approval queue
2. **Reduced sync frequency** - Only when beneficial
3. **Better performance** - No reprocessing of known events
4. **Cleaner admin interface** - Fewer false duplicates to review
5. **Smarter event detection** - Better handling of venue variations

## Rollback Plan

If issues arise, you can:

1. **Disable new workflow:** Rename `improved-sync.yml`
2. **Re-enable old workflow:** Use existing `reliable-sync.yml`
3. **Clear state:** Delete `src/sync/event_state.pkl`
4. **Manual cleanup:** Use cleanup tool to remove any issues

## Integration with Existing Scrapers

The improved system is designed to work with your existing scrapers. Update the placeholder functions in `improved_sync.py`:

```python
def scrape_willspub_events():
    # Import your existing Will's Pub scraper
    from scripts.event_sync.enhanced_multi_venue_sync import scrape_willspub_events
    return scrape_willspub_events()

def scrape_conduit_events():
    # Import your existing Conduit scraper
    from scripts.event_sync.conduit_scraper import scrape_conduit_events
    return scrape_conduit_events()
```

## Success Metrics

Track these metrics to verify the solution:

1. **Duplicate reduction:** Number of events in approval queue
2. **Sync efficiency:** Runtime reduction due to smart scheduling
3. **Processing accuracy:** Events successfully created vs skipped
4. **Admin workload:** Time spent reviewing duplicates

The improved system should dramatically reduce duplicates while maintaining reliable event discovery.
