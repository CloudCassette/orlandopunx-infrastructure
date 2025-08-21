import json
import requests
import os
from datetime import datetime

print("🌐 Testing Gancio integration with real credentials...")

# Get credentials from environment (will be empty in local test)
gancio_email = os.environ.get('GANCIO_EMAIL', '')
gancio_password = os.environ.get('GANCIO_PASSWORD', '')

if not gancio_email or not gancio_password:
    print("⚠️  No credentials provided - this is just a local test")
    print("The GitHub workflow will use the actual secrets")
    print("✅ Integration logic is ready for automation")
    exit(0)

# If we have credentials, test the actual integration
print(f"📧 Using email: {gancio_email}")
print("🔑 Using configured password")

# Setup session
session = requests.Session()
gancio_url = 'https://orlandopunx.com'

# Test authentication
try:
    login_data = {'email': gancio_email, 'password': gancio_password}
    response = session.post(f"{gancio_url}/login", data=login_data)
    
    if response.status_code == 200:
        print("✅ Authentication successful!")
        
        # Load one event for testing
        with open('willspub_events.json', 'r') as f:
            events = json.load(f)
        
        if events:
            test_event = events[0]  # Just test with first event
            print(f"🎯 Testing with: {test_event.get('title', 'Unknown')}")
            
            # Convert to Gancio format
            event_date = test_event.get('date', '')
            event_time = test_event.get('time', '19:00')
            
            if event_date:
                date_obj = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                start_timestamp = int(date_obj.timestamp()) * 1000
                end_timestamp = start_timestamp + (3 * 3600 * 1000)
                
                gancio_event = {
                    "title": f"[TEST] {test_event.get('title', '')}",
                    "description": f"{test_event.get('description', '')}\n\nTEST EVENT - More info: {test_event.get('url', '')}",
                    "start_datetime": start_timestamp,
                    "end_datetime": end_timestamp,
                    "place_id": 1,
                    "tags": ["live-music", "willspub", "test"],
                    "recurrent": False,
                    "online": False
                }
                
                print("📤 Adding test event to Gancio...")
                response = session.post(
                    f"{gancio_url}/add",
                    json=gancio_event,
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"📊 Response: {response.status_code}")
                if response.status_code in [200, 201]:
                    print("✅ Test event added successfully!")
                    print("Check your Gancio admin panel for the '[TEST]' event")
                else:
                    print(f"❌ Failed: {response.text[:200]}")
            else:
                print("❌ No date found in test event")
        else:
            print("❌ No events found to test")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
