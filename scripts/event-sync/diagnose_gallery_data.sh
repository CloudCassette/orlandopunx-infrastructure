#!/bin/bash
# Comprehensive Gallery Data Diagnostics

echo "🔍 Gallery Data Display Diagnostics"
echo "==================================="

# Function to test API data
test_api_data() {
    echo "📊 API Data Test"
    echo "==============="
    
    # Test API endpoint
    api_response=$(curl -s http://192.168.86.4:8081/api/flyers)
    
    if [ -z "$api_response" ]; then
        echo "❌ API returned empty response"
        return 1
    fi
    
    # Count flyers in API
    flyer_count=$(echo "$api_response" | jq length 2>/dev/null || echo "unknown")
    echo "📊 API Response: $flyer_count flyers found"
    
    # Show sample data structure
    echo ""
    echo "📋 Sample API Data (first 2 flyers):"
    echo "$api_response" | jq '.[0:2]' 2>/dev/null || {
        echo "Raw API sample (first 500 chars):"
        echo "$api_response" | head -c 500
        echo "..."
    }
    
    # Test specific data fields
    echo ""
    echo "🔍 Data Field Analysis:"
    for field in filename event_name size modified url; do
        if echo "$api_response" | grep -q "\"$field\""; then
            echo "  ✅ $field: Present in API"
        else
            echo "  ❌ $field: Missing from API"
        fi
    done
}

# Function to test HTML rendering
test_html_rendering() {
    echo ""
    echo "📄 HTML Rendering Test"
    echo "====================="
    
    html_content=$(curl -s http://192.168.86.4:8081/)
    
    if [ -z "$html_content" ]; then
        echo "❌ HTML page returned empty"
        return 1
    fi
    
    echo "📊 HTML Page Size: $(echo "$html_content" | wc -c) characters"
    
    # Check for key elements
    echo ""
    echo "🔍 HTML Element Check:"
    
    if echo "$html_content" | grep -q "flyer-card"; then
        flyer_cards=$(echo "$html_content" | grep -c "flyer-card")
        echo "  ✅ Flyer cards: $flyer_cards found"
    else
        echo "  ❌ No flyer cards found"
    fi
    
    if echo "$html_content" | grep -q "event-name"; then
        event_names=$(echo "$html_content" | grep -c "event-name")
        echo "  ✅ Event names: $event_names found"
    else
        echo "  ❌ No event names found"
    fi
    
    if echo "$html_content" | grep -q "file-info"; then
        file_info=$(echo "$html_content" | grep -c "file-info")
        echo "  ✅ File info: $file_info found"
    else
        echo "  ❌ No file info found"
    fi
    
    # Show sample rendered content
    echo ""
    echo "📋 Sample Rendered Event (first flyer):"
    echo "$html_content" | grep -A 10 -B 2 "event-name" | head -15
}

# Function to test CSS visibility
test_css_visibility() {
    echo ""
    echo "🎨 CSS Visibility Test"
    echo "====================="
    
    html_content=$(curl -s http://192.168.86.4:8081/)
    
    # Check for CSS that might hide text
    echo "🔍 Checking for CSS that might hide text elements:"
    
    potential_issues=0
    
    if echo "$html_content" | grep -q "color.*#fff\|color.*white" && echo "$html_content" | grep -q "background.*#fff\|background.*white"; then
        echo "  ⚠️  Potential white-on-white text issue detected"
        potential_issues=$((potential_issues + 1))
    fi
    
    if echo "$html_content" | grep -q "opacity.*0\|display.*none\|visibility.*hidden"; then
        echo "  ⚠️  Elements with visibility issues found:"
        echo "$html_content" | grep -B 5 -A 5 "opacity.*0\|display.*none\|visibility.*hidden"
        potential_issues=$((potential_issues + 1))
    fi
    
    # Check color variables
    echo ""
    echo "🌈 Color Variables Check:"
    if echo "$html_content" | grep -q "var(--text-primary)"; then
        echo "  ✅ CSS custom properties (variables) in use"
        echo "  🔍 Text colors defined:"
        echo "$html_content" | grep -o "text-primary.*#[^;]*" | head -3
    else
        echo "  📊 No CSS custom properties detected"
    fi
    
    if [ $potential_issues -eq 0 ]; then
        echo "✅ No obvious CSS visibility issues detected"
    else
        echo "⚠️  $potential_issues potential CSS issues found"
    fi
}

# Function to simulate browser DevTools checks
browser_devtools_simulation() {
    echo ""
    echo "🌐 Browser DevTools Simulation"
    echo "=============================="
    
    echo "📊 Network Request Analysis:"
    
    # Test main page request
    main_response=$(curl -s -w "HTTP %{http_code} | Size: %{size_download} bytes | Time: %{time_total}s" http://192.168.86.4:8081/)
    echo "  📄 Main page: $main_response" | tail -1
    
    # Test API request
    api_response=$(curl -s -w "HTTP %{http_code} | Size: %{size_download} bytes | Time: %{time_total}s" http://192.168.86.4:8081/api/flyers)
    echo "  📊 API endpoint: $api_response" | tail -1
    
    # Test sample image
    sample_flyer=$(curl -s http://192.168.86.4:8081/api/flyers | jq -r '.[0].filename' 2>/dev/null || echo "Kaleigh_Baker_5431b639.jpg")
    if [ ! -z "$sample_flyer" ] && [ "$sample_flyer" != "null" ]; then
        img_response=$(curl -s -w "HTTP %{http_code} | Size: %{size_download} bytes | Time: %{time_total}s" -o /dev/null "http://192.168.86.4:8081/flyers/$sample_flyer")
        echo "  🖼️  Sample flyer: $img_response"
    fi
    
    echo ""
    echo "🔧 Recommended Browser DevTools Commands:"
    echo "========================================="
    echo "1. Open http://192.168.86.4:8081 in browser"
    echo "2. Press F12 to open DevTools"
    echo "3. Check Console tab for JavaScript errors"
    echo "4. Check Network tab for failed requests"
    echo "5. Use Elements tab to inspect .flyer-card elements"
    echo "6. Check Computed styles for .event-name and .file-info"
}

# Function to provide cache refresh commands
cache_refresh_commands() {
    echo ""
    echo "🔄 Cache Refresh & Rebuild Commands"
    echo "===================================="
    
    echo "🌐 Browser Cache Refresh:"
    echo "  • Hard refresh: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)"
    echo "  • Clear browser cache: F12 → Application → Storage → Clear"
    echo "  • Private/Incognito mode test"
    
    echo ""
    echo "🔧 Server-side refresh commands:"
    echo "  # Restart gallery server:"
    echo "  scripts/event-sync/gallery_switcher.sh"
    echo ""
    echo "  # Force data refresh:"
    echo "  scripts/event-sync/monitor_flyer_delivery.sh"
    echo ""
    echo "  # Manual server restart:"
    echo "  pkill -f serve_flyers_enhanced.py"
    echo "  cd scripts/event-sync && python3 serve_flyers_enhanced.py &"
}

# Main execution
echo "🕐 $(date)"
echo ""

test_api_data
test_html_rendering  
test_css_visibility
browser_devtools_simulation
cache_refresh_commands

echo ""
echo "🎯 Summary:"
echo "==========="
echo "Based on the diagnostics above, check for:"
echo "1. ❌ API data issues (missing fields)"
echo "2. ❌ HTML rendering problems (missing elements)" 
echo "3. ❌ CSS visibility issues (hidden text)"
echo "4. ❌ Network request failures"
echo "5. ❌ Browser cache issues"
echo ""
echo "🔗 Gallery URL: http://192.168.86.4:8081"
