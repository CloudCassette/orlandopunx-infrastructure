#!/bin/bash
# Test Gallery Color Visibility

echo "🎨 Testing Gallery Color Visibility"
echo "=================================="

# Create a test HTML with the exact same CSS but exaggerated colors
cat > /tmp/gallery_color_test.html << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Color Visibility Test</title>
    <style>
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --accent-orange: #ff6b35;
            --text-primary: #fff;
            --text-secondary: #ccc;
        }
        body {
            font-family: Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
        }
        .test-section {
            background: var(--bg-secondary);
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
        }
        .event-name {
            color: var(--accent-orange);
            font-weight: 600;
            font-size: 1.1em;
        }
        .file-info {
            color: var(--text-secondary);
            font-size: 0.85em;
        }
        /* Test variations */
        .test-bright { color: #FF0000 !important; }
        .test-contrast { color: #FFFF00 !important; background: #000000 !important; }
    </style>
</head>
<body>
    <h1 style="color: var(--accent-orange);">Gallery Color Visibility Test</h1>
    
    <div class="test-section">
        <h2>Original Colors (as in gallery)</h2>
        <div class="event-name">Sample Event Name - Should be Orange</div>
        <div class="file-info">📅 2025-08-20 12:13<br>📏 465 KB<br>filename.jpg</div>
    </div>
    
    <div class="test-section">
        <h2>High Contrast Test</h2>
        <div class="event-name test-bright">Sample Event Name - Bright Red</div>
        <div class="file-info test-contrast">📅 2025-08-20 12:13<br>📏 465 KB<br>filename.jpg</div>
    </div>
    
    <div class="test-section">
        <h2>Color Values</h2>
        <p>Orange: #ff6b35 (should be visible)</p>
        <p>Light Gray: #ccc (should be visible)</p>
        <p>Background: #1a1a1a (dark gray)</p>
    </div>
</body>
</html>
HTML

echo "✅ Created color test file: /tmp/gallery_color_test.html"
echo "🌐 You can open this in your browser to test color visibility"
echo ""

# Test if we can serve it temporarily
echo "🚀 Starting temporary test server on port 8082..."
echo "   Open: http://192.168.86.4:8082"
echo "   Press Ctrl+C to stop"

cd /tmp && python3 -m http.server 8082
