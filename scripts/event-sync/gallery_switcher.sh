#!/bin/bash
# Gallery Switcher - Switch between original and enhanced gallery

echo "🖼️ Orlando Events Gallery Switcher"
echo "==================================="

# Check current gallery status
CURRENT_PID=$(pgrep -f "serve_flyers.py")
ENHANCED_PID=$(pgrep -f "serve_flyers_enhanced.py")

if [ ! -z "$CURRENT_PID" ]; then
    echo "📊 Current status: Original gallery running (PID: $CURRENT_PID)"
elif [ ! -z "$ENHANCED_PID" ]; then
    echo "📊 Current status: Enhanced gallery running (PID: $ENHANCED_PID)"
else
    echo "📊 Current status: No gallery server running"
fi

echo ""
echo "Available options:"
echo "  [1] Switch to Enhanced Gallery (Realistic Aspect Ratios)"
echo "  [2] Switch to Original Gallery (Square Thumbnails)" 
echo "  [3] Compare Both Galleries"
echo "  [4] Test Current Gallery"
echo "  [5] Quit"

read -p "Choose option (1-5): " choice

case $choice in
    1)
        echo "🚀 Switching to Enhanced Gallery..."
        
        # Stop current gallery
        if [ ! -z "$CURRENT_PID" ]; then
            kill $CURRENT_PID 2>/dev/null
            echo "  ✅ Stopped original gallery"
            sleep 2
        fi
        if [ ! -z "$ENHANCED_PID" ]; then
            kill $ENHANCED_PID 2>/dev/null
            echo "  ✅ Stopped enhanced gallery"
            sleep 2
        fi
        
        # Start enhanced gallery
        cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync
        nohup python3 serve_flyers_enhanced.py > gallery_enhanced.log 2>&1 &
        NEW_PID=$!
        
        echo "  🎸 Enhanced gallery started (PID: $NEW_PID)"
        echo "  ✨ Features: Realistic aspect ratios, enhanced design"
        echo "  🌐 Access: http://192.168.86.4:8081"
        
        # Test the new gallery
        sleep 3
        if curl -s http://192.168.86.4:8081/ > /dev/null; then
            echo "  ✅ Enhanced gallery is accessible!"
        else
            echo "  ❌ Gallery accessibility test failed"
        fi
        ;;
        
    2)
        echo "🔄 Switching to Original Gallery..."
        
        # Stop current gallery
        if [ ! -z "$CURRENT_PID" ]; then
            kill $CURRENT_PID 2>/dev/null
            echo "  ✅ Stopped original gallery"
            sleep 2
        fi
        if [ ! -z "$ENHANCED_PID" ]; then
            kill $ENHANCED_PID 2>/dev/null
            echo "  ✅ Stopped enhanced gallery"
            sleep 2
        fi
        
        # Start original gallery
        cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync
        nohup python3 serve_flyers.py > gallery_original.log 2>&1 &
        NEW_PID=$!
        
        echo "  📊 Original gallery started (PID: $NEW_PID)"
        echo "  📐 Features: Square thumbnails, compact layout"
        echo "  🌐 Access: http://192.168.86.4:8081"
        
        # Test the gallery
        sleep 3
        if curl -s http://192.168.86.4:8081/ > /dev/null; then
            echo "  ✅ Original gallery is accessible!"
        else
            echo "  ❌ Gallery accessibility test failed"
        fi
        ;;
        
    3)
        echo "📊 Gallery Comparison Mode"
        echo "========================="
        
        # Show differences
        echo "🔍 Feature Comparison:"
        echo ""
        echo "📐 Original Gallery:"
        echo "  • Fixed 200px height thumbnails"
        echo "  • Square aspect ratio (cropped)"
        echo "  • Compact grid layout"
        echo "  • object-fit: cover (crops images)"
        echo ""
        echo "✨ Enhanced Gallery:"
        echo "  • Preserved original aspect ratios"
        echo "  • No image cropping"
        echo "  • Responsive grid layout"
        echo "  • object-fit: contain (full image visible)"
        echo "  • Enhanced hover effects"
        echo "  • Better typography and spacing"
        echo "  • Mobile-responsive design"
        echo ""
        
        # Current gallery info
        if [ ! -z "$ENHANCED_PID" ]; then
            echo "🎯 Currently running: Enhanced Gallery"
        elif [ ! -z "$CURRENT_PID" ]; then
            echo "🎯 Currently running: Original Gallery"
        else
            echo "🎯 No gallery currently running"
        fi
        ;;
        
    4)
        echo "🧪 Testing Current Gallery..."
        
        # Test main page
        if curl -s -o /dev/null -w "Main page: HTTP %{http_code}, %{size_download} bytes\n" http://192.168.86.4:8081/; then
            echo "✅ Main gallery page accessible"
        else
            echo "❌ Main gallery page failed"
        fi
        
        # Test API
        if curl -s -o /dev/null -w "API: HTTP %{http_code}, %{size_download} bytes\n" http://192.168.86.4:8081/api/flyers; then
            echo "✅ API endpoint accessible"
            flyer_count=$(curl -s http://192.168.86.4:8081/api/flyers | jq length 2>/dev/null || echo "unknown")
            echo "📊 API reports $flyer_count flyers available"
        else
            echo "❌ API endpoint failed"
        fi
        
        # Test sample flyer
        sample_flyer=$(curl -s http://192.168.86.4:8081/api/flyers | jq -r '.[0].filename' 2>/dev/null)
        if [ ! -z "$sample_flyer" ] && [ "$sample_flyer" != "null" ]; then
            if curl -s -o /dev/null -w "Sample flyer: HTTP %{http_code}, %{size_download} bytes\n" "http://192.168.86.4:8081/flyers/$sample_flyer"; then
                echo "✅ Flyer downloads working"
            else
                echo "❌ Flyer download failed"
            fi
        fi
        ;;
        
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
        
    *)
        echo "❌ Invalid option selected"
        ;;
esac

echo ""
echo "🔗 Gallery URL: http://192.168.86.4:8081"
echo "📊 Use 'ps aux | grep serve_flyers' to check running processes"
