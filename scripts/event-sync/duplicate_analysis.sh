#!/bin/bash
# Duplicate Analysis and Management Tools

echo "🔍 GANCIO DUPLICATE ANALYSIS TOOLS"
echo "=================================="
echo "⏰ $(date)"

# Function to show current Gancio state
show_gancio_status() {
    echo ""
    echo "📊 Current Gancio Status:"
    echo "========================"
    
    # Get total events
    total_events=$(curl -s http://localhost:13120/api/events | jq length 2>/dev/null || echo "unknown")
    echo "   📋 Total events: $total_events"
    
    if [ "$total_events" != "unknown" ] && [ "$total_events" -gt 0 ]; then
        # Save events to temp file for analysis
        curl -s http://localhost:13120/api/events > /tmp/gancio_events.json 2>/dev/null
        
        # Count by venue
        echo "   🏢 Events by venue:"
        jq -r '.[] | .place.name // "Unknown"' /tmp/gancio_events.json 2>/dev/null | sort | uniq -c | sort -nr | while read count venue; do
            echo "      • $venue: $count events"
        done
        
        # Check for obvious duplicates
        echo ""
        echo "   🔍 Potential duplicates (same title):"
        duplicate_count=$(jq -r '.[].title' /tmp/gancio_events.json 2>/dev/null | sort | uniq -d | wc -l)
        echo "      🔴 Duplicate titles found: $duplicate_count"
        
        if [ "$duplicate_count" -gt 0 ]; then
            echo "      📋 Sample duplicates:"
            jq -r '.[].title' /tmp/gancio_events.json 2>/dev/null | sort | uniq -d | head -5 | while read title; do
                count=$(jq -r --arg title "$title" '.[] | select(.title == $title) | .id' /tmp/gancio_events.json 2>/dev/null | wc -l)
                echo "         • \"$title\" ($count copies)"
            done
        fi
    fi
}

# Function to provide quick duplicate commands
quick_duplicate_commands() {
    echo ""
    echo "🛠️ QUICK DUPLICATE ANALYSIS COMMANDS:"
    echo "====================================="
    echo ""
    echo "# 1. Analyze duplicates (safe - no changes)"
    echo "python3 scripts/event-sync/gancio_duplicate_cleanup.py"
    echo ""
    echo "# 2. List all event titles with counts"
    echo "curl -s http://localhost:13120/api/events | jq -r '.[].title' | sort | uniq -c | sort -nr"
    echo ""
    echo "# 3. Find duplicate titles only"
    echo "curl -s http://localhost:13120/api/events | jq -r '.[].title' | sort | uniq -d"
    echo ""
    echo "# 4. Count events by venue"
    echo "curl -s http://localhost:13120/api/events | jq -r '.[] | .place.name // \"Unknown\"' | sort | uniq -c"
    echo ""
    echo "# 5. Show recent events (last 10)"
    echo "curl -s http://localhost:13120/api/events | jq -r '.[] | [.id, .title, .createdAt] | @tsv' | sort -k3 -r | head -10"
}

# Function to backup events before cleanup
backup_events() {
    echo ""
    echo "💾 EVENT BACKUP:"
    echo "==============="
    
    backup_file="gancio_events_backup_$(date +%Y%m%d_%H%M%S).json"
    backup_path="scripts/event-sync/$backup_file"
    
    echo "📋 Creating backup before cleanup..."
    if curl -s http://localhost:13120/api/events > "$backup_path" 2>/dev/null; then
        event_count=$(jq length "$backup_path" 2>/dev/null || echo "unknown")
        echo "   ✅ Backup created: $backup_path"
        echo "   📊 Events backed up: $event_count"
        echo "   💡 Restore command: # Manual restore would require event recreation"
    else
        echo "   ❌ Backup failed"
    fi
}

# Function to show advanced cleanup options
advanced_cleanup_options() {
    echo ""
    echo "🔧 ADVANCED CLEANUP OPTIONS:"
    echo "============================"
    echo ""
    echo "1. 🧪 Safe Analysis (Recommended first):"
    echo "   python3 scripts/event-sync/gancio_duplicate_cleanup.py"
    echo ""
    echo "2. 🗑️ Live Cleanup (After analysis):"
    echo "   python3 scripts/event-sync/gancio_duplicate_cleanup.py --live"
    echo ""
    echo "3. 📊 Manual SQL approach (if API fails):"
    echo "   # This would require direct database access"
    echo "   # Not recommended unless API cleanup fails"
    echo ""
    echo "4. 🔄 Reset and re-sync (nuclear option):"
    echo "   # Delete all events and re-run enhanced sync"
    echo "   # Only if other methods fail"
}

# Function to show prevention setup
prevention_setup() {
    echo ""
    echo "🛡️ PREVENTION SETUP:"
    echo "==================="
    echo ""
    echo "1. ✅ Update sync scripts to use enhanced deduplication"
    echo "2. 🔧 Modify automated_sync_working_fixed.py to include prevention logic"
    echo "3. 📊 Set up monitoring to detect duplicates early"
    echo "4. 🤖 Update GitHub Actions to use prevention-enabled sync"
    echo ""
    echo "Prevention files that will be created:"
    echo "   • scripts/event-sync/duplicate_prevention.py"
    echo "   • Enhanced deduplication in sync scripts"
}

# Main menu function
show_main_menu() {
    echo ""
    echo "📋 DUPLICATE MANAGEMENT OPTIONS:"
    echo "==============================="
    echo "  [1] Show current Gancio status"
    echo "  [2] Analyze duplicates (safe)"
    echo "  [3] Backup events"
    echo "  [4] Advanced cleanup options"
    echo "  [5] Prevention setup guide"
    echo "  [6] Quick commands reference"
    echo "  [7] Exit"
    echo ""
    read -p "Choose option (1-7): " choice
    
    case $choice in
        1) show_gancio_status ;;
        2) 
            echo "🔍 Running duplicate analysis..."
            python3 scripts/event-sync/gancio_duplicate_cleanup.py
            ;;
        3) backup_events ;;
        4) advanced_cleanup_options ;;
        5) prevention_setup ;;
        6) quick_duplicate_commands ;;
        7) echo "👋 Goodbye!"; exit 0 ;;
        *) echo "❌ Invalid option"; show_main_menu ;;
    esac
    
    # Return to menu
    echo ""
    read -p "Press Enter to continue..."
    show_main_menu
}

# Check command line arguments
if [ $# -eq 0 ]; then
    # Interactive mode
    show_gancio_status
    show_main_menu
else
    # Command line mode
    case "$1" in
        "status") show_gancio_status ;;
        "analyze") python3 scripts/event-sync/gancio_duplicate_cleanup.py ;;
        "cleanup") python3 scripts/event-sync/gancio_duplicate_cleanup.py --live ;;
        "backup") backup_events ;;
        "commands") quick_duplicate_commands ;;
        *) 
            echo "Usage: $0 [status|analyze|cleanup|backup|commands]"
            echo "Or run without arguments for interactive mode"
            ;;
    esac
fi
