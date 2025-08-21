#!/usr/bin/env python3
# Enhanced Orlando Punk Events Flyer Gallery
# Preserves aspect ratios and provides better thumbnail experience

import http.server
import json
import os
import socketserver
from datetime import datetime


class EnhancedFlyerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # Generate enhanced HTML gallery
            html = self.generate_enhanced_gallery()
            self.wfile.write(html.encode())
        elif self.path == "/api/flyers":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # Return flyer list as JSON
            flyers = self.get_flyer_list()
            self.wfile.write(json.dumps(flyers).encode())
        else:
            # Serve files normally
            super().do_GET()

    def get_flyer_list(self):
        flyers = []
        flyer_dir = "flyers"
        if os.path.exists(flyer_dir):
            for file in os.listdir(flyer_dir):
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    filepath = os.path.join(flyer_dir, file)
                    stat = os.stat(filepath)

                    # Extract event name from filename
                    event_name = file.replace("_", " ").split(".")[0]

                    flyers.append(
                        {
                            "filename": file,
                            "event_name": event_name,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "url": f"/flyers/{file}",
                        }
                    )

        return sorted(flyers, key=lambda x: x["modified"], reverse=True)

    def generate_enhanced_gallery(self):
        flyers = self.get_flyer_list()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Orlando Punk Events - Enhanced Flyer Gallery</title>
    <style>
        :root {{
            --bg-primary: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --accent-orange: #ff6b35;
            --accent-hover: #e5562d;
            --text-primary: #fff;
            --text-secondary: #ccc;
            --border-color: #444;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}

        h1 {{
            color: var(--accent-orange);
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}

        .subtitle {{
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 30px;
            font-style: italic;
        }}

        .stats {{
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        /* Enhanced Gallery Grid */
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }}

        /* Flyer Card with Realistic Proportions */
        .flyer-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border-color);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
            height: fit-content;
        }}

        .flyer-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.3);
            border-color: var(--accent-orange);
        }}

        /* Image Container with Aspect Ratio Preservation */
        .flyer-image-container {{
            width: 100%;
            margin-bottom: 15px;
            border-radius: 8px;
            overflow: hidden;
            background: #000;
            position: relative;
        }}

        .flyer-card img {{
            width: 100%;
            height: auto;
            display: block;
            border-radius: 8px;
            transition: transform 0.3s ease;
            /* Preserve aspect ratio - no cropping */
            object-fit: contain;
            background: #000;
        }}

        .flyer-card:hover img {{
            transform: scale(1.02);
        }}

        /* Flyer Information */
        .flyer-info {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}

        .event-name {{
            font-weight: 600;
            color: var(--accent-orange);
            margin-bottom: 8px;
            font-size: 1.1em;
            line-height: 1.3;
        }}

        .file-info {{
            font-size: 0.85em;
            color: var(--text-secondary);
            margin-bottom: 15px;
            line-height: 1.4;
        }}

        .file-info .filename {{
            word-break: break-all;
            margin-top: 5px;
            color: #aaa;
            font-family: monospace;
            font-size: 0.8em;
        }}

        /* Enhanced Download Button */
        .download-btn {{
            background: linear-gradient(135deg, var(--accent-orange), #ff8c5a);
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-top: auto;
            font-weight: 500;
            transition: all 0.3s ease;
            text-align: center;
        }}

        .download-btn:hover {{
            background: linear-gradient(135deg, var(--accent-hover), #e5562d);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4);
        }}

        .download-btn::before {{
            content: "⬇ ";
            margin-right: 5px;
        }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            h1 {{
                font-size: 2em;
            }}

            .gallery {{
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }}

            .flyer-card {{
                padding: 15px;
            }}
        }}

        @media (max-width: 480px) {{
            .gallery {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Loading Animation */
        .loading {{
            text-align: center;
            color: var(--text-secondary);
            padding: 40px;
        }}

        .loading::after {{
            content: "";
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--accent-orange);
            animation: spin 1s ease-in-out infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <h1>🎸 Orlando Punk Events</h1>
    <div class="subtitle">Enhanced Flyer Gallery - Preserving Original Proportions</div>

    <div class="stats">
        <strong>Collection Stats:</strong> {len(flyers)} flyers |
        Total size: {sum(f['size'] for f in flyers) / 1024 / 1024:.1f} MB |
        <span style="color: var(--accent-orange);">Realistic Aspect Ratios</span>
    </div>

    <div class="gallery" id="gallery">
"""

        for flyer in flyers:
            # Clean up event name for better display
            clean_name = flyer["event_name"].replace("_", " ").title()

            html += f"""
        <div class="flyer-card">
            <div class="flyer-image-container">
                <img src="{flyer['url']}" alt="{clean_name}" loading="lazy">
            </div>
            <div class="flyer-info">
                <div class="event-name">{clean_name}</div>
                <div class="file-info">
                    📅 {flyer['modified']}<br>
                    📏 {flyer['size'] // 1024} KB<br>
                    <div class="filename">{flyer['filename']}</div>
                </div>
                <a href="{flyer['url']}" class="download-btn" download>Download Original</a>
            </div>
        </div>
"""

        html += """
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🎸 Enhanced Orlando Punk Events Flyer Gallery loaded!');

            // Add image load error handling
            const images = document.querySelectorAll('.flyer-card img');
            images.forEach(img => {
                img.addEventListener('error', function() {
                    this.parentElement.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Image not available</div>';
                });

                img.addEventListener('load', function() {
                    this.parentElement.style.opacity = '1';
                });
            });

            // Add hover effects for better UX
            const cards = document.querySelectorAll('.flyer-card');
            cards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.zIndex = '10';
                });

                card.addEventListener('mouseleave', function() {
                    this.style.zIndex = '1';
                });
            });

            console.log(`Loaded ${images.length} flyer images with preserved aspect ratios`);
        });
    </script>
</body>
</html>
"""
        return html


if __name__ == "__main__":
    PORT = 8081

    # Change to the event-sync directory
    os.chdir("/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync")

    with socketserver.TCPServer(("", PORT), EnhancedFlyerHandler) as httpd:
        print(f"🎸 Enhanced Flyer Gallery Server starting on port {PORT}")
        print(f"✨ Realistic aspect ratios preserved!")
        print(f"🌐 Access from your laptop: http://192.168.86.4:{PORT}")
        print(f"📱 Responsive design for all devices")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("🛑 Enhanced flyer gallery server stopped")
