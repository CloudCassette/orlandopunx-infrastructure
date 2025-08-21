#!/bin/bash
# Conduit-Gancio Sync Monitoring and Terminal Commands

echo "🔧 Conduit-Gancio Sync Monitoring Tools"
echo "======================================="

# Function to check Gancio service status
check_gancio_status() {
    echo ""
    echo "📊 Gancio Service Status:"
    echo "========================"
    systemctl is-active gancio && echo "   ✅ Service is active" || echo "   ❌ Service is not active"
    
    # Check if accessible
    if curl -s http://localhost:13120/ > /dev/null; then
        echo "   ✅ Web interface accessible"
    else
        echo "   ❌ Web interface not accessible"
    fi
    
    # Check event count
    event_count=$(curl -s http://localhost:13120/api/events | jq length 2>/dev/null || echo "unknown")
    echo "   📋 Current events in Gancio: $event_count"
}

# Function to tail Gancio logs
tail_gancio_logs() {
    echo ""
    echo "📋 Tailing Gancio Logs (Press Ctrl+C to stop):"
    echo "=============================================="
    echo "Looking for sync activity..."
    
    # Try multiple log locations
    if journalctl -u gancio -f --no-pager 2>/dev/null; then
        :
    elif [ -f /var/log/gancio.log ]; then
        tail -f /var/log/gancio.log
    else
        echo "❌ Could not find Gancio logs"
        echo "💡 Try: sudo journalctl -u gancio -f"
    fi
}

# Function to check sync script status
check_sync_status() {
    echo ""
    echo "🤖 Sync Script Analysis:"
    echo "========================"
    
    echo "📄 Main sync script (automated_sync_working.py):"
    if [ -f scripts/event-sync/automated_sync_working.py ]; then
        echo "   ✅ Found"
        venue_support=$(grep -c "conduit\|Conduit" scripts/event-sync/automated_sync_working.py || echo "0")
        echo "   🎯 Conduit references: $venue_support"
        
        if [ "$venue_support" -eq 0 ]; then
            echo "   ❌ No Conduit support in main sync script"
        else
            echo "   ✅ Has Conduit references"
        fi
    else
        echo "   ❌ Main sync script not found"
    fi
    
    echo ""
    echo "📄 Enhanced multi-venue script:"
    if [ -f scripts/event-sync/enhanced_multi_venue_sync_with_conduit.py ]; then
        echo "   ✅ Found enhanced script with Conduit support"
    else
        echo "   ❌ Enhanced script not found"
    fi
}

# Function to test API manually
test_conduit_api() {
    echo ""
    echo "🧪 Manual Conduit Event Test:"
    echo "============================="
    
    echo "📊 Checking Conduit scraper..."
    cd scripts/event-sync
    
    if python3 -c "from conduit_scraper import scrape_conduit_events; print(f'✅ Scraper working: {len(scrape_conduit_events(download_images=False))} events found')" 2>/dev/null; then
        :
    else
        echo "❌ Conduit scraper test failed"
        return 1
    fi
    
    echo ""
    echo "📊 Sample Conduit event data:"
    python3 -c "
from conduit_scraper import scrape_conduit_events
import json
events = scrape_conduit_events(download_images=False)
if events:
    print('📋 First Conduit event:')
    print(json.dumps(events[0], indent=2, default=str))
else:
    print('❌ No events found')
" 2>/dev/null
}

# Function to compare gallery vs Gancio events
compare_events() {
    echo ""
    echo "📊 Gallery vs Gancio Event Comparison:"
    echo "====================================="
    
    # Count Conduit flyers in gallery
    conduit_gallery=$(ls scripts/event-sync/flyers/conduit-*.jpg 2>/dev/null | wc -l)
    echo "   📸 Conduit flyers in gallery: $conduit_gallery"
    
    # Count events in Gancio
    gancio_total=$(curl -s http://localhost:13120/api/events | jq length 2>/dev/null || echo "unknown")
    echo "   📋 Total events in Gancio: $gancio_total"
    
    # Try to identify Conduit events in Gancio (this might not work without proper venue filtering)
    echo "   🔍 Note: Cannot easily filter Conduit events from Gancio API without venue info"
    
    echo ""
    echo "📋 Recent gallery additions (last 5 Conduit flyers):"
    ls -lt scripts/event-sync/flyers/conduit-*.jpg 2>/dev/null | head -5 | while read line; do
        filename=$(echo "$line" | awk '{print $9}')
        date=$(echo "$line" | awk '{print $6, $7, $8}')
        echo "   • $(basename "$filename") - $date"
    done
}

# Function to check environment variables
check_environment() {
    echo ""
    echo "🔐 Environment Variables Check:"
    echo "=============================="
    
    if [ -n "$GANCIO_EMAIL" ]; then
        echo "   ✅ GANCIO_EMAIL: $GANCIO_EMAIL"
    else
        echo "   ❌ GANCIO_EMAIL not set"
    fi
    
    if [ -n "$GANCIO_PASSWORD" ]; then
        echo "   ✅ GANCIO_PASSWORD: (set, ${#GANCIO_PASSWORD} characters)"
    else
        echo "   ❌ GANCIO_PASSWORD not set"
        echo "   💡 Set with: export GANCIO_PASSWORD='your_password'"
    fi
}

# Function to run enhanced sync script
run_enhanced_sync() {
    echo ""
    echo "🚀 Running Enhanced Multi-Venue Sync:"
    echo "===================================="
    
    if [ -f scripts/event-sync/enhanced_multi_venue_sync_with_conduit.py ]; then
        echo "Starting enhanced sync with Conduit support..."
        cd scripts/event-sync
        python3 enhanced_multi_venue_sync_with_conduit.py
    else
        echo "❌ Enhanced sync script not found"
        echo "💡 Run: python3 scripts/event-sync/fix_conduit_gancio_sync.py"
    fi
}

# Main menu function
show_menu() {
    echo ""
    echo "🛠️ Available Commands:"
    echo "====================="
    echo "  [1] Check Gancio Status"
    echo "  [2] Tail Gancio Logs"
    echo "  [3] Check Sync Status"
    echo "  [4] Test Conduit API"
    echo "  [5] Compare Events (Gallery vs Gancio)"
    echo "  [6] Check Environment Variables"
    echo "  [7] Run Enhanced Sync"
    echo "  [8] All Diagnostics"
    echo "  [9] Quit"
    echo ""
    read -p "Choose option (1-9): " choice
    
    case $choice in
        1) check_gancio_status ;;
        2) tail_gancio_logs ;;
        3) check_sync_status ;;
        4) test_conduit_api ;;
        5) compare_events ;;
        6) check_environment ;;
        7) run_enhanced_sync ;;
        8) 
            check_gancio_status
            check_sync_status
            test_conduit_api
            compare_events
            check_environment
            ;;
        9) echo "👋 Goodbye!"; exit 0 ;;
        *) echo "❌ Invalid option"; show_menu ;;
    esac
    
    show_menu
}

# Check if running interactively or with specific command
if [ $# -eq 0 ]; then
    # No arguments - show interactive menu
    show_menu
else
    # Command line arguments provided
    case "$1" in
        "status") check_gancio_status ;;
        "logs") tail_gancio_logs ;;
        "sync") check_sync_status ;;
        "test") test_conduit_api ;;
        "compare") compare_events ;;
        "env") check_environment ;;
        "run") run_enhanced_sync ;;
        "all") 
            check_gancio_status
            check_sync_status
            test_conduit_api
            compare_events
            check_environment
            ;;
        *) 
            echo "Usage: $0 [status|logs|sync|test|compare|env|run|all]"
            echo "Or run without arguments for interactive menu"
            ;;
    esac
fi
