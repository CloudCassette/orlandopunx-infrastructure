#!/usr/bin/env python3
"""
🧹 Gancio Queue Manager - Find and Clean Approval Queue
====================================================
Comprehensive tool to find and manage pending/draft events in Gancio
"""

import requests
import json
import os
import sys
from bs4 import BeautifulSoup
import re
from datetime import datetime

class GancioQueueManager:
    def __init__(self):
        self.base_url = "http://localhost:13120"
        self.public_url = "https://orlandopunx.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
    def authenticate(self):
        """Authenticate with Gancio"""
        email = os.getenv('GANCIO_EMAIL', 'godlessamericarecords@gmail.com')
        password = os.getenv('GANCIO_PASSWORD')
        
        if not password:
            print("❌ Missing GANCIO_PASSWORD")
            return False
            
        print(f"🔑 Authenticating as {email}...")
        
        try:
            # Try local login first
            response = self.session.post(f"{self.base_url}/login", data={
                'email': email,
                'password': password
            }, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Local authentication successful")
                return True
                
            # Try public URL
            response = self.session.post(f"{self.public_url}/login", data={
                'email': email,
                'password': password
            }, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Public authentication successful")
                return True
                
            print(f"❌ Authentication failed: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def find_admin_endpoints(self):
        """Discover admin endpoints and pending events"""
        print("\n🔍 DISCOVERING ADMIN ENDPOINTS")
        print("="*50)
        
        endpoints_to_try = [
            "/admin",
            "/admin/events",
            "/admin/events/pending",
            "/admin/events/draft", 
            "/admin/events/moderation",
            "/events/admin",
            "/events/pending",
            "/events/draft",
            "/events/moderation",
            "/moderation",
            "/moderation/events",
            "/api/admin/events",
            "/api/events/admin",
            "/api/events/pending",
            "/api/events/draft",
            "/api/events/moderation",
            "/api/events?all=true&status=pending",
            "/api/events?all=true&status=draft",
            "/api/events?all=true&approved=false",
            "/api/events?all=true&is_visible=false"
        ]
        
        found_endpoints = {}
        
        for endpoint in endpoints_to_try:
            try:
                for base_url in [self.base_url, self.public_url]:
                    url = f"{base_url}{endpoint}"
                    response = self.session.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'json' in content_type:
                            try:
                                data = response.json()
                                if isinstance(data, list):
                                    count = len(data)
                                    found_endpoints[endpoint] = {
                                        'url': url,
                                        'type': 'json',
                                        'count': count,
                                        'sample': data[:2] if count > 0 else []
                                    }
                                    print(f"✅ {endpoint}: {count} items (JSON)")
                                else:
                                    found_endpoints[endpoint] = {
                                        'url': url,
                                        'type': 'json_object', 
                                        'data': data
                                    }
                                    print(f"✅ {endpoint}: JSON object")
                            except:
                                pass
                        else:
                            # HTML response - look for event-related content
                            content = response.text.lower()
                            if any(word in content for word in ['event', 'pending', 'draft', 'moderat']):
                                found_endpoints[endpoint] = {
                                    'url': url,
                                    'type': 'html',
                                    'contains_events': True
                                }
                                print(f"✅ {endpoint}: HTML page (has event content)")
                                
            except Exception as e:
                pass  # Skip errors
        
        return found_endpoints
    
    def analyze_hidden_events(self):
        """Look for events that might be hidden/pending"""
        print("\n🔍 ANALYZING HIDDEN/PENDING EVENTS")
        print("="*50)
        
        try:
            # Check for events with is_visible=false
            response = self.session.get(f"{self.base_url}/api/events?all=true")
            if response.status_code == 200:
                all_events = response.json()
                
                visible_events = [e for e in all_events if e.get('is_visible', True)]
                hidden_events = [e for e in all_events if not e.get('is_visible', True)]
                
                print(f"📊 Total events: {len(all_events)}")
                print(f"👁️  Visible events: {len(visible_events)}")
                print(f"🔒 Hidden events: {len(hidden_events)}")
                
                if hidden_events:
                    print("\n🔒 HIDDEN EVENTS FOUND:")
                    for i, event in enumerate(hidden_events[:5]):  # Show first 5
                        title = event.get('title', 'No title')
                        created = event.get('createdAt', 'Unknown')
                        print(f"   {i+1}. {title} (created: {created})")
                    
                    if len(hidden_events) > 5:
                        print(f"   ... and {len(hidden_events) - 5} more")
                    
                return hidden_events
                
        except Exception as e:
            print(f"❌ Error analyzing events: {e}")
            return []
    
    def scrape_admin_pages(self):
        """Scrape admin pages for pending event info"""
        print("\n🕸️ SCRAPING ADMIN PAGES")
        print("="*50)
        
        admin_urls = [
            f"{self.base_url}/admin",
            f"{self.public_url}/admin", 
            f"{self.base_url}/admin/events",
            f"{self.public_url}/admin/events"
        ]
        
        for url in admin_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for event counts or pending indicators
                    text = soup.get_text().lower()
                    
                    # Search for numbers that might indicate pending events
                    pending_patterns = [
                        r'pending[:\s]*(\d+)',
                        r'draft[:\s]*(\d+)', 
                        r'awaiting[:\s]*approval[:\s]*(\d+)',
                        r'moderation[:\s]*(\d+)',
                        r'(\d+)[:\s]*pending',
                        r'(\d+)[:\s]*draft'
                    ]
                    
                    for pattern in pending_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            for match in matches:
                                count = int(match)
                                if count > 20:  # Likely candidate for the 162 events
                                    print(f"🎯 FOUND POTENTIAL QUEUE: {count} events at {url}")
                                    print(f"   Pattern matched: {pattern}")
                                    
                                    # Try to find the specific page/endpoint
                                    links = soup.find_all('a', href=True)
                                    for link in links:
                                        href = link['href']
                                        link_text = link.get_text().lower()
                                        if any(word in link_text for word in ['pending', 'draft', 'moderate']):
                                            full_url = urljoin(url, href)
                                            print(f"   📋 Related link: {full_url}")
                    
                    # Look for admin navigation
                    nav_links = soup.find_all('a', href=True)
                    admin_links = []
                    for link in nav_links:
                        href = link['href']
                        text = link.get_text().lower()
                        if any(word in text for word in ['event', 'pending', 'draft', 'moderat', 'admin']):
                            admin_links.append((urljoin(url, href), text.strip()))
                    
                    if admin_links:
                        print(f"🔗 Admin links found at {url}:")
                        for link_url, link_text in admin_links[:10]:  # Show first 10
                            print(f"   • {link_text}: {link_url}")
                            
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
    
    def comprehensive_search(self):
        """Run comprehensive search for the approval queue"""
        print("🕵️ COMPREHENSIVE GANCIO QUEUE SEARCH")
        print("="*60)
        
        if not self.authenticate():
            return False
            
        # Step 1: Try API endpoints
        endpoints = self.find_admin_endpoints()
        
        # Step 2: Analyze hidden events
        hidden_events = self.analyze_hidden_events()
        
        # Step 3: Scrape admin pages
        self.scrape_admin_pages()
        
        # Summary
        print("\n📋 SEARCH SUMMARY")
        print("="*50)
        print(f"🔍 Admin endpoints found: {len(endpoints)}")
        print(f"🔒 Hidden events found: {len(hidden_events)}")
        
        if hidden_events:
            print(f"\n💡 RECOMMENDATION: There are {len(hidden_events)} hidden events.")
            print("These might be your 'pending' events that need approval.")
            print("Run the bulk approval tool to make them visible.")
        
        return len(hidden_events) > 0

def main():
    manager = GancioQueueManager()
    manager.comprehensive_search()

if __name__ == "__main__":
    main()
