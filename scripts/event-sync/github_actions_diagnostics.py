#!/usr/bin/env python3
"""
GitHub Actions Diagnostics Script
Tests connectivity and authentication for GitHub Actions environment
"""

import requests
import os
import sys
from datetime import datetime

def test_gancio_connectivity():
    """Test basic connectivity to Gancio"""
    base_url = os.getenv('GANCIO_BASE_URL', 'http://localhost:13120')
    
    print(f"🔍 Testing Gancio connectivity to: {base_url}")
    
    try:
        # Test basic API endpoint
        response = requests.get(f"{base_url}/api/events", timeout=10)
        
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Gancio API accessible - Found {len(events)} events")
            return True
        else:
            print(f"❌ Gancio API returned status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_authentication():
    """Test Gancio authentication"""
    base_url = os.getenv('GANCIO_BASE_URL', 'http://localhost:13120')
    email = os.getenv('GANCIO_EMAIL')
    password = os.getenv('GANCIO_PASSWORD')
    
    if not email or not password:
        print("⚠️ No authentication credentials provided")
        return False
    
    print(f"🔐 Testing authentication for: {email}")
    
    session = requests.Session()
    try:
        # Get login page first
        login_page = session.get(f"{base_url}/login", timeout=10)
        if login_page.status_code != 200:
            print(f"❌ Cannot access login page: {login_page.status_code}")
            return False
        
        # Attempt login
        login_response = session.post(f"{base_url}/auth/login", data={
            'email': email,
            'password': password
        }, allow_redirects=True, timeout=10)
        
        if 'admin' in login_response.url:
            print("✅ Authentication successful - redirected to admin")
            return True
        elif login_response.status_code == 200:
            print("✅ Authentication successful - status 200")
            return True
        else:
            print(f"❌ Authentication failed: {login_response.status_code}")
            print(f"Final URL: {login_response.url}")
            print(f"Response preview: {login_response.text[:300]}...")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return False

def environment_info():
    """Print environment information"""
    print("📊 Environment Information:")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Python Version: {sys.version}")
    print(f"   GANCIO_BASE_URL: {os.getenv('GANCIO_BASE_URL', 'Not set')}")
    print(f"   GANCIO_EMAIL: {os.getenv('GANCIO_EMAIL', 'Not set')}")
    print(f"   GANCIO_PASSWORD: {'Set' if os.getenv('GANCIO_PASSWORD') else 'Not set'}")
    
    # Test required modules
    print("\n📦 Module Check:")
    modules = ['requests', 'json', 'os', 'sys']
    for module in modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (missing)")

def main():
    print("🚀 GitHub Actions Gancio Diagnostics")
    print("=" * 50)
    
    # Print environment info
    environment_info()
    
    # Test connectivity
    print(f"\n🔍 Connectivity Tests:")
    connectivity_ok = test_gancio_connectivity()
    
    # Test authentication
    print(f"\n🔐 Authentication Tests:")
    auth_ok = test_authentication()
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    print(f"   Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if connectivity_ok and auth_ok:
        print(f"\n🎉 All tests passed - Gancio is accessible and authentication works!")
        return 0
    else:
        print(f"\n⚠️ Some tests failed - check the details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
