#!/bin/bash
# Live Gallery Testing Tools

echo "🧪 Live Gallery Testing & CSS Inspector"
echo "======================================="

# Function to test thumbnail rendering
test_thumbnail_rendering() {
    echo "🖼️ Thumbnail Rendering Test"
    echo "=========================="
    
    # Get first few flyers for testing
    echo "📊 Testing thumbnail display for sample flyers:"
    
    flyers=$(curl -s http://192.168.86.4:8081/api/flyers | jq -r '.[0:3].[].filename' 2>/dev/null)
    
    if [ -z "$flyers" ]; then
        echo "❌ Could not fetch flyer list from API"
        return 1
    fi
    
    count=1
    for flyer in $flyers; do
        echo "  $count. Testing: $flyer"
        
        # Test direct image access
        if curl -s -o /dev/null -w "     Status: HTTP %{http_code}, Size: %{size_download} bytes\n" "http://192.168.86.4:8081/flyers/$flyer"; then
            echo "     ✅ Image accessible"
        else
            echo "     ❌ Image not accessible"
        fi
        
        count=$((count + 1))
    done
}

# Function to inspect CSS changes
inspect_css_changes() {
    echo "🎨 CSS Change Inspector"
    echo "======================"
    
    # Check which gallery is running
    if pgrep -f "serve_flyers_enhanced.py" > /dev/null; then
        echo "✨ Enhanced gallery detected - Aspect ratio preservation enabled"
        echo ""
        echo "🔍 Key CSS Features:"
        echo "  • object-fit: contain (preserves aspect ratio)"
        echo "  • height: auto (dynamic height)"
        echo "  • Responsive grid layout"
        echo "  • Enhanced hover effects"
        echo ""
    elif pgrep -f "serve_flyers.py" > /dev/null; then
        echo "📐 Original gallery detected - Fixed square thumbnails"
        echo ""
        echo "🔍 Key CSS Features:"
        echo "  • object-fit: cover (crops to square)"
        echo "  • height: 200px (fixed height)"
        echo "  • Basic grid layout"
        echo ""
    else
        echo "❌ No gallery server running"
        return 1
    fi
    
    # Test page load and inspect HTML structure
    echo "📄 HTML Structure Analysis:"
    page_content=$(curl -s http://192.168.86.4:8081/ 2>/dev/null)
    
    if echo "$page_content" | grep -q "object-fit: contain"; then
        echo "  ✅ Aspect ratio preservation CSS found"
    elif echo "$page_content" | grep -q "object-fit: cover"; then
        echo "  📐 Square thumbnail CSS found"
    else
        echo "  ⚠️  Unknown CSS configuration"
    fi
    
    if echo "$page_content" | grep -q "Enhanced Flyer Gallery"; then
        echo "  ✨ Enhanced gallery version confirmed"
    else
        echo "  📊 Standard gallery version confirmed"
    fi
}

# Function to monitor refresh after sync
monitor_refresh_after_sync() {
    echo "🔄 Sync Refresh Monitor"
    echo "======================="
    
    # Check last modification time of flyers
    echo "📅 Flyer directory status:"
    flyer_dir="/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/flyers"
    
    if [ -d "$flyer_dir" ]; then
        latest_flyer=$(ls -t "$flyer_dir"/*.jpg 2>/dev/null | head -1)
        if [ ! -z "$latest_flyer" ]; then
            echo "  📁 Latest flyer: $(basename "$latest_flyer")"
            echo "  🕐 Modified: $(stat -c %y "$latest_flyer" | cut -d. -f1)"
            
            # Check if it appears in the gallery API
            latest_filename=$(basename "$latest_flyer")
            if curl -s http://192.168.86.4:8081/api/flyers | grep -q "$latest_filename"; then
                echo "  ✅ Latest flyer appears in gallery API"
            else
                echo "  ⚠️  Latest flyer not yet in gallery API"
            fi
        else
            echo "  ❌ No flyers found"
        fi
    else
        echo "  ❌ Flyer directory not found"
    fi
    
    # Check GitHub Actions runner workspace for comparison
    runner_dir="/home/cloudcassette/actions-runner/_work/orlandopunx-infrastructure/orlandopunx-infrastructure/scripts/event-sync/flyers"
    if [ -d "$runner_dir" ]; then
        runner_latest=$(ls -t "$runner_dir"/*.jpg 2>/dev/null | head -1)
        if [ ! -z "$runner_latest" ]; then
            echo "  📂 Runner workspace latest: $(basename "$runner_latest")"
            echo "  🕐 Modified: $(stat -c %y "$runner_latest" | cut -d. -f1)"
        fi
    fi
}

# Function to benchmark page load performance
benchmark_performance() {
    echo "⚡ Performance Benchmark"
    echo "======================="
    
    echo "🏃 Testing page load times:"
    
    # Test main gallery page
    time_main=$(curl -s -o /dev/null -w "%{time_total}" http://192.168.86.4:8081/)
    echo "  📄 Main gallery page: ${time_main}s"
    
    # Test API endpoint
    time_api=$(curl -s -o /dev/null -w "%{time_total}" http://192.168.86.4:8081/api/flyers)
    echo "  📊 API endpoint: ${time_api}s"
    
    # Test sample image
    sample_flyer=$(curl -s http://192.168.86.4:8081/api/flyers | jq -r '.[0].filename' 2>/dev/null)
    if [ ! -z "$sample_flyer" ] && [ "$sample_flyer" != "null" ]; then
        time_image=$(curl -s -o /dev/null -w "%{time_total}" "http://192.168.86.4:8081/flyers/$sample_flyer")
        echo "  🖼️  Sample image: ${time_image}s"
    fi
    
    echo ""
    echo "📊 Performance Analysis:"
    if (( $(echo "$time_main < 0.5" | bc -l 2>/dev/null || echo "0") )); then
        echo "  ✅ Main page load: Excellent (< 0.5s)"
    elif (( $(echo "$time_main < 1.0" | bc -l 2>/dev/null || echo "0") )); then
        echo "  👍 Main page load: Good (< 1.0s)"
    else
        echo "  ⚠️  Main page load: Could be improved (> 1.0s)"
    fi
}

# Main menu
echo ""
echo "Available tests:"
echo "  [1] Test Thumbnail Rendering"
echo "  [2] Inspect CSS Changes"
echo "  [3] Monitor Sync Refresh"
echo "  [4] Benchmark Performance"
echo "  [5] Run All Tests"
echo "  [6] Quit"

read -p "Choose test (1-6): " choice

case $choice in
    1) test_thumbnail_rendering ;;
    2) inspect_css_changes ;;
    3) monitor_refresh_after_sync ;;
    4) benchmark_performance ;;
    5) 
        echo "🏃 Running all tests..."
        echo ""
        test_thumbnail_rendering
        echo ""
        inspect_css_changes
        echo ""
        monitor_refresh_after_sync
        echo ""
        benchmark_performance
        ;;
    6) echo "👋 Goodbye!"; exit 0 ;;
    *) echo "❌ Invalid option" ;;
esac

echo ""
echo "🔗 Gallery URL: http://192.168.86.4:8081"
echo "🛠️  Switch galleries with: scripts/event-sync/gallery_switcher.sh"
