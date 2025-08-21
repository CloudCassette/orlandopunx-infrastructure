#!/bin/bash
# Monitor flyer delivery and web server status

echo "🖼️ Orlando Events Flyer Delivery Monitor"
echo "========================================"

# Function to check flyer counts
check_flyer_counts() {
    local runner_count=$(find /home/cloudcassette/actions-runner/_work/orlandopunx-infrastructure/orlandopunx-infrastructure/scripts/event-sync/flyers -name "*.jpg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | wc -l)
    local local_count=$(find /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/flyers -name "*.jpg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | wc -l)
    
    echo "📊 Flyer Counts:"
    echo "  GitHub Actions workspace: $runner_count flyers"
    echo "  Local web server: $local_count flyers"
    
    if [ "$runner_count" -gt "$local_count" ]; then
        echo "  ⚠️ Web server missing $((runner_count - local_count)) flyers"
        return 1
    elif [ "$local_count" -gt "$runner_count" ]; then
        echo "  ✅ Web server has $((local_count - runner_count)) additional flyers"
        return 0
    else
        echo "  ✅ Flyer counts are synchronized"
        return 0
    fi
}

# Function to test web server
test_web_server() {
    echo ""
    echo "🌐 Web Server Status:"
    
    if pgrep -f "serve_flyers.py" > /dev/null; then
        echo "  ✅ Flyer web server is running (PID: $(pgrep -f serve_flyers.py))"
        
        # Test API endpoint
        if curl -s --connect-timeout 5 http://192.168.86.4:8081/api/flyers > /dev/null; then
            echo "  ✅ API endpoint responding"
            
            # Get flyer count from API
            api_count=$(curl -s http://192.168.86.4:8081/api/flyers | jq length 2>/dev/null || echo "unknown")
            echo "  📊 API reports $api_count flyers available"
        else
            echo "  ❌ API endpoint not responding"
        fi
        
        # Test main gallery
        if curl -s --connect-timeout 5 http://192.168.86.4:8081/ > /dev/null; then
            echo "  ✅ Gallery page accessible"
        else
            echo "  ❌ Gallery page not accessible"
        fi
    else
        echo "  ❌ Flyer web server not running"
        echo "  💡 To start: cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync && python3 serve_flyers.py &"
    fi
}

# Function to sync missing flyers
sync_missing_flyers() {
    echo ""
    echo "🔄 Syncing Missing Flyers:"
    
    source_dir="/home/cloudcassette/actions-runner/_work/orlandopunx-infrastructure/orlandopunx-infrastructure/scripts/event-sync/flyers"
    target_dir="/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/flyers"
    
    if [ -d "$source_dir" ] && [ -d "$target_dir" ]; then
        before_count=$(find "$target_dir" -name "*.jpg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | wc -l)
        
        echo "  📁 Syncing from: $source_dir"
        echo "  📁 Syncing to: $target_dir"
        
        rsync -av --update "$source_dir/" "$target_dir/"
        chmod 644 "$target_dir"/*.{jpg,png,gif} 2>/dev/null || true
        
        after_count=$(find "$target_dir" -name "*.jpg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | wc -l)
        new_files=$((after_count - before_count))
        
        echo "  ✅ Sync completed: $new_files new files added"
    else
        echo "  ❌ Source or target directory not found"
    fi
}

# Main monitoring function
main() {
    echo "🕐 $(date)"
    echo ""
    
    check_flyer_counts
    sync_needed=$?
    
    test_web_server
    
    if [ $sync_needed -ne 0 ]; then
        echo ""
        echo "🚨 Synchronization needed!"
        
        read -p "Sync missing flyers now? (y/n): " -n 1 choice
        echo ""
        if [[ $choice == [Yy] ]]; then
            sync_missing_flyers
            echo ""
            echo "🔄 Re-checking after sync:"
            check_flyer_counts
        fi
    fi
    
    echo ""
    echo "🔗 Access your flyer gallery at: http://192.168.86.4:8081"
}

# Run main function
main "$@"
