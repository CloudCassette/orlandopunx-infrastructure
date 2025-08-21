#!/usr/bin/env python3
"""
📥 Create Downloadable Files
===========================
Package Conduit events for easy download
"""

import json
import os
import zipfile
from datetime import datetime


def create_downloadable_package():
    """Create downloadable package"""

    print("📦 Creating downloadable package...")

    # Create a zip file with all import files
    with zipfile.ZipFile("conduit_events_package.zip", "w") as zipf:

        # Add summary file
        if os.path.exists("conduit_events_summary.txt"):
            zipf.write("conduit_events_summary.txt")
            print("✅ Added summary file")

        # Add individual import files
        import_files = [
            f
            for f in os.listdir(".")
            if f.startswith("conduit_import_") and f.endswith(".txt")
        ]
        for file in sorted(import_files):
            zipf.write(file)

        print(f"✅ Added {len(import_files)} individual event files")

        # Add JSON file for reference
        if os.path.exists("conduit_events.json"):
            zipf.write("conduit_events.json")
            print("✅ Added JSON data file")

    # Get file size
    zip_size = os.path.getsize("conduit_events_package.zip")
    print(f"📦 Package created: conduit_events_package.zip ({zip_size} bytes)")

    # Create a simple HTML index
    with open("index.html", "w") as f:
        f.write(
            """<!DOCTYPE html>
<html>
<head>
    <title>Conduit Events - Manual Import Files</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        h1 { color: #ff6e40; }
        .file-list { background: #2a2a2a; padding: 15px; border-radius: 5px; }
        a { color: #ff6e40; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .summary { background: #333; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🎸 Conduit Events - Manual Import Files</h1>

    <div class="summary">
        <h2>📋 Quick Access</h2>
        <p><strong><a href="conduit_events_summary.txt">📄 Events Summary</a></strong> - Overview of all 19 events</p>
        <p><strong><a href="conduit_events_package.zip">📦 Download All Files</a></strong> - Complete package</p>
    </div>

    <div class="file-list">
        <h2>📁 Individual Event Files</h2>"""
        )

        # List all import files
        import_files = [
            f
            for f in os.listdir(".")
            if f.startswith("conduit_import_") and f.endswith(".txt")
        ]
        for i, file in enumerate(sorted(import_files), 1):
            # Extract event name from filename
            event_name = (
                file.replace("conduit_import_", "")
                .replace(".txt", "")
                .replace("_", " ")
            )
            f.write(f'        <p>{i:2d}. <a href="{file}">{event_name}</a></p>\n')

        f.write(
            """    </div>

    <div class="summary">
        <h2>📋 Instructions for Manual Import</h2>
        <ol>
            <li>Go to your Gancio admin panel</li>
            <li>Click the + button to add new events</li>
            <li>Copy/paste info from each .txt file</li>
            <li>Set venue to "Conduit" (6700 Aloma Ave)</li>
            <li>Upload flyers from the flyers directory if needed</li>
        </ol>
    </div>

    <p><em>Generated: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</em></p>
</body>
</html>"""
        )

    print("✅ Created index.html with file listing")


if __name__ == "__main__":
    create_downloadable_package()
