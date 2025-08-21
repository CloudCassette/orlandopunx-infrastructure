#!/bin/bash

# Safe archival of redundant files (no downtime approach)
# Only archives files that are clearly redundant or backup versions

set -e

echo "🗃️ SAFE ARCHIVAL OF REDUNDANT FILES"
echo "=================================="

ARCHIVE_DIR="archive/old-scripts"

# Files that are clearly redundant (test/debug/temp files)
SAFE_TO_ARCHIVE=(
    "scripts/event-sync/test_gancio_integration.py"
    "scripts/event-sync/test_one_gancio_event.py" 
    "scripts/event-sync/temp_gancio_integration.py"
    "scripts/event-sync/check_anonymous_events.py"
    "scripts/event-sync/check_current_events.py"
    "scripts/event-sync/compare_scraped_vs_existing.py"
    "scripts/event-sync/investigate_gancio_api.py"
    "scripts/event-sync/preview_fixed_events.py"
    "scripts/event-sync/fix_flyer_detection.py"
)

# Files that are alternative versions (keeping the working ones)
ALTERNATIVE_VERSIONS=(
    "scripts/event-sync/enhanced_multi_venue_sync_fixed.py"
    "scripts/event-sync/songkick_scraper_fixed.py"
    "scripts/event-sync/sync_to_gancio_fixed.py"
    "scripts/event-sync/willspub_scraper_fixed.py"
    "scripts/event-sync/willspub_to_gancio_with_fixed_scraper.py"
)

echo "📋 Archiving test/debug files..."
for file in "${SAFE_TO_ARCHIVE[@]}"; do
    if [ -f "$file" ]; then
        echo "  📦 $file"
        mv "$file" "$ARCHIVE_DIR/"
    else
        echo "  ⚠️  $file not found (already moved?)"
    fi
done

echo "📋 Archiving alternative versions..."  
for file in "${ALTERNATIVE_VERSIONS[@]}"; do
    if [ -f "$file" ]; then
        echo "  📦 $file"
        mv "$file" "$ARCHIVE_DIR/"
    else
        echo "  ⚠️  $file not found (already moved?)"
    fi
done

echo "✅ Safe archival complete!"
echo "🔒 Production files preserved:"
echo "  - scripts/event-sync/automated_sync_working.py"
echo "  - scripts/event-sync/enhanced_multi_venue_sync.py"
echo "  - scripts/event-sync/test_current_functionality.py"

