#!/usr/bin/env python3
"""
Enhanced Flyer Gallery with Improved Text Visibility
"""

import json
import os
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer


class EnhancedGalleryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.serve_gallery()
        elif self.path == "/api/flyers":
            self.serve_api()
        elif self.path.startswith("/flyers/"):
            self.serve_flyer()
        else:
            self.send_error(404)

    def serve_gallery(self):
        flyers_dir = os.path.join(os.getcwd(), "scripts", "event-sync", "flyers")
        flyers = self.get_flyer_data(flyers_dir)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orlando Punx Event Flyers - Enhanced Visibility</title>
    <style>
        :root {{
            --bg-primary: #0f0f0f;
            --bg-secondary: #1e1e1e;
            --accent-orange: #ff7b45;
            --accent-hover: #ff9065;
            --text-primary: #ffffff;
            --text-secondary: #e0e0e0;
            --text-muted: #b0b0b0;
            --border-color: #333;
            --shadow-color: rgba(255, 123, 69, 0.2);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        h1 {{
            color: var(--accent-orange);
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
            font-weight: 700;
        }}

        .subtitle {{
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 30px;
            font-style: italic;
            font-size: 1.1em;
        }}

        .stats {{
            text-align: center;
            margin-bottom: 30px;
            padding: 15px;
            background: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .flyer-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 20px;
            border: 2px solid var(--border-color);
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            height: fit-content;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}

        .flyer-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 30px var(--shadow-color);
            border-color: var(--accent-orange);
            background: #252525;
        }}

        .flyer-image-container {{
            width: 100%;
            margin-bottom: 15px;
            border-radius: 8px;
            overflow: hidden;
            background: #000;
            position: relative;
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .flyer-image-container img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}

        .flyer-card:hover .flyer-image-container img {{
            transform: scale(1.05);
        }}

        .flyer-info {{
            flex-grow: 1;
        }}

        .event-name {{
            font-weight: 700;
            color: var(--accent-orange);
            margin-bottom: 12px;
            font-size: 1.2em;
            line-height: 1.3;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            /* Enhanced visibility */
            background: rgba(0,0,0,0.3);
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 4px solid var(--accent-orange);
        }}

        .file-info {{
            font-size: 0.9em;
            color: var(--text-secondary);
            line-height: 1.5;
            /* Enhanced visibility */
            background: rgba(0,0,0,0.2);
            padding: 10px 12px;
            border-radius: 6px;
            border-left: 2px solid var(--text-muted);
        }}

        .filename {{
            color: var(--text-muted);
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            margin-top: 5px;
            word-break: break-all;
        }}

        .download-btn {{
            display: inline-block;
            margin-top: 15px;
            padding: 12px 20px;
            background: linear-gradient(135deg, var(--accent-orange), var(--accent-hover));
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            text-align: center;
            transition: all 0.3s ease;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}

        .download-btn:hover {{
            background: linear-gradient(135deg, var(--accent-hover), #ffb085);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 123, 69, 0.4);
        }}

        /* Visibility Debug Mode */
        .debug-mode .event-name {{
            outline: 2px solid #ff0000;
            background: rgba(255, 0, 0, 0.1) !important;
        }}

        .debug-mode .file-info {{
            outline: 2px solid #00ff00;
            background: rgba(0, 255, 0, 0.1) !important;
        }}

        /* High contrast mode */
        @media (prefers-contrast: high) {{
            .event-name {{
                color: #ffaa00;
                background: #000;
            }}
            .file-info {{
                color: #fff;
                background: #111;
            }}
        }}

        .debug-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-orange);
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            z-index: 1000;
        }}

        .visibility-note {{
            background: #ffeb3b;
            color: #000;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <button class="debug-toggle" onclick="toggleDebugMode()">Debug Mode</button>

    <h1>Orlando Punx Event Flyers</h1>
    <div class="subtitle">Enhanced Visibility Gallery</div>

    <div class="visibility-note">
        🔍 If you can't see event names or file info below, press the Debug Mode button or use browser DevTools (F12)
    </div>

    <div class="stats">
        <strong>📊 Gallery Stats:</strong> {len(flyers)} flyers available |
        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>

    <div class="gallery-grid">
"""

        for flyer in flyers:
            event_name = flyer["event_name"].replace("_", " ").title()
            size_mb = flyer["size"] / (1024 * 1024)
            size_text = (
                f"{size_mb:.1f} MB" if size_mb >= 1 else f"{flyer['size'] // 1024} KB"
            )

            html += f"""        <div class="flyer-card">
            <div class="flyer-image-container">
                <img src="{flyer['url']}" alt="{event_name}" loading="lazy">
            </div>
            <div class="flyer-info">
                <div class="event-name">{event_name}</div>
                <div class="file-info">
                    📅 {flyer['modified']}<br>
                    📏 {size_text}<br>
                    <div class="filename">{flyer['filename']}</div>
                </div>
                <a href="{flyer['url']}" class="download-btn" download>Download Original</a>
            </div>
        </div>

"""

        html += """    </div>

    <script>
        let debugMode = false;

        function toggleDebugMode() {
            debugMode = !debugMode;
            document.body.classList.toggle('debug-mode', debugMode);
            document.querySelector('.debug-toggle').textContent = debugMode ? 'Normal Mode' : 'Debug Mode';

            if (debugMode) {
                console.log('🔍 Debug mode enabled - event names and file info should have colored outlines');

                // Log visibility stats
                const eventNames = document.querySelectorAll('.event-name');
                const fileInfos = document.querySelectorAll('.file-info');
                console.log(`📊 Found ${eventNames.length} event names and ${fileInfos.length} file info sections`);

                // Check computed styles
                eventNames.forEach((el, i) => {
                    if (i < 3) { // Log first 3
                        const styles = window.getComputedStyle(el);
                        console.log(`Event ${i+1} color:`, styles.color, 'background:', styles.backgroundColor);
                    }
                });
            }
        }

        // Auto-enable debug mode if URL has ?debug
        if (window.location.search.includes('debug')) {
            toggleDebugMode();
        }

        // Log initial load info
        console.log('🎨 Gallery loaded with enhanced visibility CSS');
        console.log('🔗 Add ?debug to URL to auto-enable debug mode');
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_api(self):
        flyers_dir = os.path.join(os.getcwd(), "scripts", "event-sync", "flyers")
        flyers = self.get_flyer_data(flyers_dir)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(flyers, indent=2).encode())

    def serve_flyer(self):
        filename = os.path.basename(
            urllib.parse.unquote(self.path[8:])
        )  # Remove '/flyers/'
        filepath = os.path.join(
            os.getcwd(), "scripts", "event-sync", "flyers", filename
        )

        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
                self.send_header("Content-type", "image/jpeg")
            elif filename.lower().endswith(".png"):
                self.send_header("Content-type", "image/png")
            else:
                self.send_header("Content-type", "application/octet-stream")

            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)

    def get_flyer_data(self, flyers_dir):
        if not os.path.exists(flyers_dir):
            return []

        flyers = []
        for filename in os.listdir(flyers_dir):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                filepath = os.path.join(flyers_dir, filename)
                stat = os.stat(filepath)

                # Extract event name from filename
                event_name = filename
                if "_" in filename:
                    # Remove hash suffix if present
                    parts = filename.rsplit("_", 1)
                    if (
                        len(parts[1]) == 12
                        and parts[1]
                        .replace(".jpg", "")
                        .replace(".jpeg", "")
                        .replace(".png", "")
                        .isalnum()
                    ):
                        event_name = parts[0]

                # Remove extension
                event_name = os.path.splitext(event_name)[0]

                flyers.append(
                    {
                        "filename": filename,
                        "event_name": event_name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "url": f"/flyers/{filename}",
                    }
                )

        # Sort by modification time (newest first)
        flyers.sort(key=lambda x: x["modified"], reverse=True)
        return flyers

    def log_message(self, format, *args):
        # Reduce logging noise
        if "GET /" in format % args or "GET /api" in format % args:
            return
        super().log_message(format, *args)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8081), EnhancedGalleryHandler)
    print(f"🎨 Enhanced Flyer Gallery Server running on http://192.168.86.4:8081")
    print("✨ Features:")
    print("   • Enhanced text visibility with backgrounds")
    print("   • Debug mode button (or add ?debug to URL)")
    print("   • High contrast support")
    print("   • Better color schemes")
    print("   • Console logging for troubleshooting")
    print("\nPress Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
