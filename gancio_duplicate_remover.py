#!/usr/bin/env python3

import requests
import re
import time
import json
from collections import defaultdict
from urllib.parse import urljoin

class GancioAPI:
    def __init__(self, base_url, email, password):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        
    def login(self):
        """Login to Gancio admin interface"""
        print(f"Logging in to {self.base_url}...")
        
        # First, get the login page to extract any CSRF tokens or session info
        login_page = self.session.get(f"{self.base_url}/login")
        if login_page.status_code != 200:
            raise Exception(f"Failed to access login page: {login_page.status_code}")
        
        # Extract CSRF token if present
        csrf_match = re.search(r'name=["\']_token["\'] value=["\']([^"\']+)["\']', login_page.text)
        if csrf_match:
            self.csrf_token = csrf_match.group(1)
            print(f"Found CSRF token: {self.csrf_token[:10]}...")
        
        # Attempt login via form submission
        login_data = {
            'email': self.email,
            'password': self.password
        }
        
        if self.csrf_token:
            login_data['_token'] = self.csrf_token
            
        # Try different login endpoints
        login_endpoints = ['/login', '/auth/login', '/api/auth/login']
        
        for endpoint in login_endpoints:
            print(f"Trying login endpoint: {endpoint}")
            login_response = self.session.post(
                f"{self.base_url}{endpoint}",
                data=login_data,
                allow_redirects=False
            )
            
            print(f"Login response: {login_response.status_code}")
            
            # Check if we got redirected (successful login) or got admin access
            if login_response.status_code in [302, 303]:
                print("Login successful - got redirect")
                return True
            elif login_response.status_code == 200:
                # Check if we're now logged in by accessing admin page
                admin_response = self.session.get(f"{self.base_url}/admin")
                if admin_response.status_code == 200 and 'admin' in admin_response.text.lower():
                    print("Login successful - admin access confirmed")
                    return True
                    
        # Try JSON login
        print("Trying JSON login...")
        json_login = self.session.post(
            f"{self.base_url}/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if json_login.status_code in [200, 302]:
            admin_response = self.session.get(f"{self.base_url}/admin")
            if admin_response.status_code == 200:
                print("JSON login successful")
                return True
        
        print("All login attempts failed")
        return False
    
    def get_unconfirmed_events(self):
        """Fetch unconfirmed events from admin interface"""
        print("Fetching unconfirmed events...")
        
        # Try different endpoints for unconfirmed events
        endpoints = [
            '/admin/events/unconfirmed',
            '/api/admin/events/unconfirmed', 
            '/api/events/unconfirmed',
            '/admin'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                print(f"Trying {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    # Check if this contains event data
                    if 'unconfirmedEvents' in response.text:
                        print(f"Found events data in {endpoint}")
                        return self.parse_events_from_html(response.text)
                    elif response.headers.get('content-type', '').startswith('application/json'):
                        try:
                            data = response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f"Found JSON events in {endpoint}")
                                return data
                        except:
                            pass
            except Exception as e:
                print(f"Error accessing {endpoint}: {e}")
        
        return []
    
    def parse_events_from_html(self, html_content):
        """Parse events from HTML page containing __NUXT__ data"""
        events = []
        
        # Find all events in the unconfirmedEvents array
        pattern = r'\{id:(\d+),title:([^,]+),slug:"([^"]+)"[^}]*\}'
        matches = re.findall(pattern, html_content)
        
        for match in matches:
            event_id, title_var, slug = match
            events.append({
                'id': int(event_id),
                'title_var': title_var,
                'slug': slug
            })
        
        return events
    
    def delete_event(self, event_id):
        """Delete an event by ID"""
        print(f"Attempting to delete event {event_id}...")
        
        # Try different delete endpoints
        delete_endpoints = [
            f'/api/admin/events/{event_id}',
            f'/api/events/{event_id}', 
            f'/admin/events/{event_id}/delete',
            f'/admin/events/{event_id}'
        ]
        
        for endpoint in delete_endpoints:
            try:
                # Try DELETE method
                response = self.session.delete(f"{self.base_url}{endpoint}")
                print(f"DELETE {endpoint}: {response.status_code}")
                
                if response.status_code in [200, 204, 404]:
                    return True
                    
                # Try POST method with delete action
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    data={'_method': 'DELETE', 'action': 'delete'}
                )
                print(f"POST delete {endpoint}: {response.status_code}")
                
                if response.status_code in [200, 204, 302]:
                    return True
                    
            except Exception as e:
                print(f"Error deleting via {endpoint}: {e}")
        
        return False

def analyze_duplicates(events):
    """Analyze events for duplicates based on slug patterns"""
    base_slug_groups = defaultdict(list)
    
    for event in events:
        base_slug = re.sub(r'-\d+$', '', event['slug'])
        base_slug_groups[base_slug].append(event)
    
    # Find duplicates - keep the first one, mark others for deletion
    duplicates_to_delete = []
    kept_originals = []
    
    for base_slug, event_list in base_slug_groups.items():
        if len(event_list) > 1:
            # Sort by ID to keep the earliest one
            event_list.sort(key=lambda x: x['id'])
            kept_originals.append(event_list[0])
            duplicates_to_delete.extend(event_list[1:])  # All but the first
        else:
            kept_originals.append(event_list[0])
    
    return duplicates_to_delete, kept_originals

def main():
    # Configuration
    BASE_URL = "https://orlandopunx.com"
    EMAIL = "admin"
    PASSWORD = "OrlandoPunkShows2024!"
    
    # Modes
    DRY_RUN = True  # Set to False to actually delete events
    BATCH_SIZE = 10  # Number of events to delete in each batch
    DELAY_BETWEEN_DELETES = 2  # Seconds to wait between deletions
    
    try:
        # Initialize API client
        api = GancioAPI(BASE_URL, EMAIL, PASSWORD)
        
        # Login
        if not api.login():
            print("❌ Failed to login. Check credentials.")
            return
        
        print("✅ Successfully logged in")
        
        # Get events
        events = api.get_unconfirmed_events()
        if not events:
            print("❌ Could not fetch events")
            return
            
        print(f"📊 Found {len(events)} total events")
        
        # Analyze duplicates
        duplicates_to_delete, kept_originals = analyze_duplicates(events)
        
        print(f"\n📈 Analysis Results:")
        print(f"   Total events: {len(events)}")
        print(f"   Unique events to keep: {len(kept_originals)}")
        print(f"   Duplicate events to delete: {len(duplicates_to_delete)}")
        
        if not duplicates_to_delete:
            print("✅ No duplicates found!")
            return
        
        # Show sample of what will be deleted
        print(f"\n🗑️  Sample of events that will be deleted:")
        for i, event in enumerate(duplicates_to_delete[:10]):
            print(f"   {i+1}. ID: {event['id']}, Slug: {event['slug']}")
        if len(duplicates_to_delete) > 10:
            print(f"   ... and {len(duplicates_to_delete) - 10} more")
        
        # Confirmation
        if DRY_RUN:
            print(f"\n🔍 DRY RUN MODE - No events will actually be deleted")
            print(f"   Set DRY_RUN = False in the script to perform actual deletions")
            return
        else:
            print(f"\n⚠️  WARNING: This will delete {len(duplicates_to_delete)} events!")
            response = input("Are you sure you want to continue? (type 'YES' to confirm): ")
            if response != 'YES':
                print("❌ Cancelled by user")
                return
        
        # Delete duplicates in batches
        deleted_count = 0
        failed_count = 0
        
        print(f"\n🚀 Starting deletion of {len(duplicates_to_delete)} duplicate events...")
        
        for i, event in enumerate(duplicates_to_delete):
            print(f"\n[{i+1}/{len(duplicates_to_delete)}] ", end="")
            
            if api.delete_event(event['id']):
                deleted_count += 1
                print(f"✅ Deleted event {event['id']} ({event['slug']})")
            else:
                failed_count += 1
                print(f"❌ Failed to delete event {event['id']} ({event['slug']})")
            
            # Add delay between deletions
            if (i + 1) % BATCH_SIZE == 0:
                print(f"   💤 Batch complete, sleeping {DELAY_BETWEEN_DELETES} seconds...")
                time.sleep(DELAY_BETWEEN_DELETES)
        
        # Final results
        print(f"\n📊 Cleanup Results:")
        print(f"   Successfully deleted: {deleted_count}")
        print(f"   Failed to delete: {failed_count}")
        print(f"   Remaining events: {len(kept_originals) + failed_count}")
        
        if deleted_count > 0:
            print(f"✅ Cleanup completed! Removed {deleted_count} duplicate events.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
