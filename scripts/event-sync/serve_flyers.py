#!/usr/bin/env python3
# Orlando Punk Events Flyer Gallery
# Simple HTTP server to browse and download flyer images from your laptop

import http.server
import socketserver
import os
import json
from datetime import datetime

class FlyerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Generate HTML gallery
            html = self.generate_gallery()
            self.wfile.write(html.encode())
        elif self.path == '/api/flyers':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Return flyer list as JSON
            flyers = self.get_flyer_list()
            self.wfile.write(json.dumps(flyers).encode())
        else:
            # Serve files normally
            super().do_GET()
    
    def get_flyer_list(self):
        flyers = []
        flyer_dir = 'flyers'
        if os.path.exists(flyer_dir):
            for file in os.listdir(flyer_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    filepath = os.path.join(flyer_dir, file)
                    stat = os.stat(filepath)
                    
                    # Extract event name from filename
                    event_name = file.replace('_', ' ').split('.')[0]
                    
                    flyers.append({
                        'filename': file,
                        'event_name': event_name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'url': f'/flyers/{file}'
                    })
        
        return sorted(flyers, key=lambda x: x['modified'], reverse=True)
    
    def generate_gallery(self):
        flyers = self.get_flyer_list()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Orlando Punk Events - Flyer Gallery</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
        h1 {{ color: #ff6b35; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }}
        .flyer-card {{ background: #2a2a2a; border-radius: 8px; padding: 15px; border: 1px solid #444; }}
        .flyer-card img {{ width: 100%; height: 200px; object-fit: cover; border-radius: 5px; }}
        .flyer-info {{ margin-top: 10px; }}
        .event-name {{ font-weight: bold; color: #ff6b35; margin-bottom: 5px; }}
        .file-info {{ font-size: 12px; color: #ccc; }}
        .download-btn {{ background: #ff6b35; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; display: inline-block; margin-top: 5px; }}
        .download-btn:hover {{ background: #e5562d; }}
        .stats {{ background: #333; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Orlando Punk Events - Flyer Gallery</h1>
    
    <div class="stats">
        <strong>Collection Stats:</strong> {len(flyers)} flyers | 
        Total size: {sum(f['size'] for f in flyers) / 1024 / 1024:.1f} MB
    </div>
    
    <div class="gallery">
"""
        
        for flyer in flyers:
            html += f"""
        <div class="flyer-card">
            <img src="{flyer['url']}" alt="{flyer['event_name']}" loading="lazy">
            <div class="flyer-info">
                <div class="event-name">{flyer['event_name']}</div>
                <div class="file-info">
                    {flyer['modified']} | {flyer['size'] // 1024} KB<br>
                    {flyer['filename']}
                </div>
                <a href="{flyer['url']}" class="download-btn" download>Download</a>
            </div>
        </div>
"""
        
        html += """
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Orlando Punk Events Flyer Gallery loaded!');
        });
    </script>
</body>
</html>
"""
        return html

if __name__ == "__main__":
    PORT = 8081
    
    # Change to the event-sync directory
    os.chdir('/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync')
    
    with socketserver.TCPServer(("", PORT), FlyerHandler) as httpd:
        print(f"Flyer Gallery Server starting on port {PORT}")
        print(f"Access from your laptop: http://192.168.86.4:{PORT}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Flyer gallery server stopped")
