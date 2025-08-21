#!/usr/bin/env python3
"""
Enhance the existing scraper to also push events to Gancio automatically
"""

import os
import re

# Read the current enhanced script
with open("enhanced_willspub_sync.py", "r") as f:
    content = f.read()

# Add Gancio imports after the existing imports
imports_addition = """import getpass
from datetime import datetime, timedelta"""

# Find where imports end and add the new ones
import_section = content.find("class EnhancedWillsPubSync:")
content = (
    content[:import_section] + imports_addition + "\n\n" + content[import_section:]
)

# Add Gancio authentication and event creation methods before the existing methods
gancio_methods = '''
    def authenticate_gancio(self, gancio_url, email=None, password=None):
        """Authenticate with Gancio using environment variables or parameters"""
        self.gancio_base_url = gancio_url.rstrip('/')

        # Get credentials from environment or parameters
        gancio_email = email or os.environ.get('GANCIO_EMAIL')
        gancio_password = password or os.environ.get('GANCIO_PASSWORD')

        if not gancio_email or not gancio_password:
            print("⚠️  No Gancio credentials provided - skipping website updates")
            return False

        try:
            login_data = {
                'email': gancio_email,
                'password': gancio_password
            }

            response = self.session.post(f"{self.gancio_base_url}/login", data=login_data, allow_redirects=True)

            if response.status_code == 200:
                print("✅ Gancio authentication successful!")
                self.gancio_authenticated = True
                return True
            else:
                print(f"❌ Gancio authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Gancio authentication error: {e}")
            return False

    def add_event_to_gancio(self, event):
        """Add a single event to Gancio"""
        if not hasattr(self, 'gancio_authenticated') or not self.gancio_authenticated:
            return False

        try:
            # Convert date string to timestamp
            event_date = event.get('date', '')
            event_time = event.get('time', '19:00')

            # Parse the date
            if event_date:
                # Assuming format is YYYY-MM-DD
                date_obj = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                start_timestamp = int(date_obj.timestamp()) * 1000  # Gancio uses milliseconds
                end_timestamp = start_timestamp + (3 * 3600 * 1000)  # 3 hours later
            else:
                print(f"   ❌ No date for event: {event.get('title', 'Unknown')}")
                return False

            # Prepare event data for Gancio
            gancio_event = {
                "title": event.get('title', ''),
                "description": event.get('description', ''),
                "start_datetime": start_timestamp,
                "end_datetime": end_timestamp,
                "place_id": 1,  # Will's Pub place ID
                "tags": ["live-music", "willspub"],
                "recurrent": False,
                "online": False
            }

            # Add source URL to description
            if event.get('url'):
                gancio_event['description'] += f"\\n\\nMore info: {event['url']}"

            print(f"   📤 Adding to Gancio: {event.get('title', 'Unknown')}")

            response = self.session.post(
                f"{self.gancio_base_url}/add",
                data=json.dumps(gancio_event),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code in [200, 201]:
                print(f"   ✅ Added to Gancio: {event.get('title', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Failed to add to Gancio: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error adding to Gancio: {e}")
            return False

'''

# Find where to insert the new methods (after __init__ method)
init_end = content.find("    def download_flyer(")
content = content[:init_end] + gancio_methods + content[init_end:]

# Update the main sync method to optionally push to Gancio
old_main_pattern = (
    r'(if __name__ == "__main__":.*?syncer = EnhancedWillsPubSync\(discord_webhook\))'
)
new_main = """if __name__ == "__main__":
    # Get Discord webhook from environment or command line
    discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')

    # Get Gancio configuration
    gancio_url = os.environ.get('GANCIO_URL', 'https://orlandopunx.com')
    gancio_email = os.environ.get('GANCIO_EMAIL')
    gancio_password = os.environ.get('GANCIO_PASSWORD')

    syncer = EnhancedWillsPubSync(discord_webhook)

    # Authenticate with Gancio if credentials are provided
    if gancio_email and gancio_password:
        print("🌐 Connecting to Gancio...")
        syncer.authenticate_gancio(gancio_url, gancio_email, gancio_password)"""

content = re.sub(old_main_pattern, new_main, content, flags=re.DOTALL)

# Also update the sync_events method to push to Gancio after finding new events
sync_pattern = r"(\s+)(# Post to Discord[\s\S]*?successfully posted.*?\n)"
gancio_addition = r"""\1\2\1
\1        # Add new events to Gancio if authenticated
\1        if hasattr(self, 'gancio_authenticated') and self.gancio_authenticated:
\1            print("🌐 Adding events to orlandopunx.com...")
\1            gancio_added = 0
\1            for event in unique_events:
\1                if self.add_event_to_gancio(event):
\1                    gancio_added += 1
\1
\1            if gancio_added > 0:
\1                summary_lines.append(f"🌐 Added {gancio_added} events to orlandopunx.com")
\1                print(f"✅ Added {gancio_added} events to orlandopunx.com")
\1            else:
\1                print("⚠️  No events were added to orlandopunx.com")
\1
"""

content = re.sub(sync_pattern, gancio_addition, content, flags=re.DOTALL)

# Write the enhanced script
with open("enhanced_willspub_sync.py", "w") as f:
    f.write(content)

print("✅ Enhanced scraper with Gancio integration!")
