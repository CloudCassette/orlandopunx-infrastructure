# Add Gancio integration to the enhanced scraper

# Read current script
with open('scripts/event-sync/enhanced_willspub_sync_with_gancio.py', 'r') as f:
    lines = f.readlines()

# Find where to insert Gancio methods (after __init__)
insert_index = -1
for i, line in enumerate(lines):
    if 'def download_flyer(' in line:
        insert_index = i
        break

if insert_index == -1:
    print("Could not find insertion point")
    exit(1)

# Gancio methods to insert
gancio_methods = [
    "    def authenticate_gancio(self, gancio_url, email=None, password=None):\n",
    "        \"\"\"Authenticate with Gancio using environment variables\"\"\"\n",
    "        self.gancio_base_url = gancio_url.rstrip('/')\n",
    "        self.gancio_authenticated = False\n",
    "        \n",
    "        gancio_email = email or os.environ.get('GANCIO_EMAIL')\n",
    "        gancio_password = password or os.environ.get('GANCIO_PASSWORD')\n",
    "        \n",
    "        if not gancio_email or not gancio_password:\n",
    "            print(\"⚠️  No Gancio credentials - skipping website integration\")\n",
    "            return False\n",
    "        \n",
    "        try:\n",
    "            login_data = {'email': gancio_email, 'password': gancio_password}\n",
    "            response = self.session.post(f\"{self.gancio_base_url}/login\", data=login_data)\n",
    "            \n",
    "            if response.status_code == 200:\n",
    "                print(\"✅ Gancio authentication successful!\")\n",
    "                self.gancio_authenticated = True\n",
    "                return True\n",
    "            else:\n",
    "                print(f\"❌ Gancio auth failed: {response.status_code}\")\n",
    "                return False\n",
    "        except Exception as e:\n",
    "            print(f\"❌ Gancio auth error: {e}\")\n",
    "            return False\n",
    "    \n",
    "    def add_event_to_gancio(self, event):\n",
    "        \"\"\"Add event to Gancio\"\"\"\n",
    "        if not getattr(self, 'gancio_authenticated', False):\n",
    "            return False\n",
    "            \n",
    "        try:\n",
    "            from datetime import datetime\n",
    "            \n",
    "            event_date = event.get('date', '')\n",
    "            event_time = event.get('time', '19:00')\n",
    "            \n",
    "            if event_date:\n",
    "                date_obj = datetime.strptime(f\"{event_date} {event_time}\", \"%Y-%m-%d %H:%M\")\n",
    "                start_timestamp = int(date_obj.timestamp()) * 1000\n",
    "                end_timestamp = start_timestamp + (3 * 3600 * 1000)\n",
    "            else:\n",
    "                return False\n",
    "            \n",
    "            gancio_event = {\n",
    "                \"title\": event.get('title', ''),\n",
    "                \"description\": event.get('description', '') + f\"\\n\\nMore info: {event.get('url', '')}\",\n",
    "                \"start_datetime\": start_timestamp,\n",
    "                \"end_datetime\": end_timestamp,\n",
    "                \"place_id\": 1,\n",
    "                \"tags\": [\"live-music\", \"willspub\"],\n",
    "                \"recurrent\": False,\n",
    "                \"online\": False\n",
    "            }\n",
    "            \n",
    "            response = self.session.post(\n",
    "                f\"{self.gancio_base_url}/add\",\n",
    "                json=gancio_event,\n",
    "                headers={'Content-Type': 'application/json'}\n",
    "            )\n",
    "            \n",
    "            if response.status_code in [200, 201]:\n",
    "                print(f\"   ✅ Added to website: {event.get('title', 'Unknown')}\")\n",
    "                return True\n",
    "            else:\n",
    "                print(f\"   ❌ Failed to add: {response.status_code}\")\n",
    "                return False\n",
    "                \n",
    "        except Exception as e:\n",
    "            print(f\"   ❌ Error: {e}\")\n",
    "            return False\n",
    "    \n",
]

# Insert the Gancio methods
lines[insert_index:insert_index] = gancio_methods

# Update the main section to include Gancio setup
main_start = -1
for i, line in enumerate(lines):
    if 'if __name__ == "__main__":' in line:
        main_start = i
        break

if main_start != -1:
    # Find the syncer creation line
    for i in range(main_start, len(lines)):
        if 'syncer = EnhancedWillsPubSync(' in lines[i]:
            # Insert Gancio setup before sync_events call
            gancio_setup = [
                "    \n",
                "    # Gancio setup\n",
                "    gancio_url = os.environ.get('GANCIO_URL', 'https://orlandopunx.com')\n",
                "    if os.environ.get('GANCIO_EMAIL') and os.environ.get('GANCIO_PASSWORD'):\n",
                "        print(\"🌐 Setting up Gancio integration...\")\n",
                "        syncer.authenticate_gancio(gancio_url)\n",
                "    \n",
            ]
            
            # Find the sync_events call
            for j in range(i, len(lines)):
                if 'syncer.sync_events()' in lines[j]:
                    lines[j:j] = gancio_setup
                    break
            break

# Add Gancio integration to sync_events method
for i, line in enumerate(lines):
    if 'successfully posted to Discord' in line:
        # Add Gancio integration after Discord posting
        gancio_integration = [
            "            \n",
            "            # Add events to Gancio if authenticated\n",
            "            if getattr(self, 'gancio_authenticated', False) and unique_events:\n",
            "                print(\"🌐 Adding events to orlandopunx.com...\")\n",
            "                gancio_added = 0\n",
            "                for event in unique_events:\n",
            "                    if self.add_event_to_gancio(event):\n",
            "                        gancio_added += 1\n",
            "                \n",
            "                if gancio_added > 0:\n",
            "                    summary_lines.append(f\"🌐 Added {gancio_added} events to orlandopunx.com\")\n",
            "                    print(f\"✅ Added {gancio_added} events to orlandopunx.com\")\n",
            "            \n",
        ]
        lines[i+1:i+1] = gancio_integration
        break

# Write the enhanced script
with open('scripts/event-sync/enhanced_willspub_sync_with_gancio.py', 'w') as f:
    f.writelines(lines)

print("✅ Created enhanced script with Gancio integration!")
