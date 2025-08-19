#!/bin/bash
#
🔔 Auto Flyer Notifications
===========================
Automatically sync new flyers and optionally notify you
#

FLYER_DIR="/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/flyers"
LAST_COUNT_FILE="/tmp/flyer_count.txt"

# Get current count
CURRENT_COUNT=$(ls -1 "$FLYER_DIR"/*.jpg 2>/dev/null | wc -l)

# Get previous count
if [ -f "$LAST_COUNT_FILE" ]; then
    PREVIOUS_COUNT=$(cat "$LAST_COUNT_FILE")
else
    PREVIOUS_COUNT=0
fi

# Check if new flyers were added
if [ "$CURRENT_COUNT" -gt "$PREVIOUS_COUNT" ]; then
    NEW_FLYERS=$((CURRENT_COUNT - PREVIOUS_COUNT))
    echo "🎸 $NEW_FLYERS new flyers added!"
    
    # Update count
    echo "$CURRENT_COUNT" > "$LAST_COUNT_FILE"
    
    # Optional: Send notification (uncomment if you want)
    # echo "New Orlando punk flyers available at http://192.168.86.4:8080" | mail -s "New Event Flyers" your@email.com
    
    # Optional: Auto-sync to laptop (uncomment and configure)
    # ./sync_flyers_to_laptop.sh
else
    echo "📊 No new flyers ($CURRENT_COUNT total)"
fi
