#!/usr/bin/env python3
"""
Advanced GitHub Actions Debugging Script
Deep dive into connectivity, authentication, and environment issues
"""

import json
import os
import sys
import time
import urllib.parse
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AdvancedGancioDebugger:
    def __init__(self):
        self.base_url = os.getenv("GANCIO_BASE_URL", "http://localhost:13120")
        self.email = os.getenv("GANCIO_EMAIL")
        self.password = os.getenv("GANCIO_PASSWORD")
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set reasonable timeout
        self.timeout = 30

    def print_environment_details(self):
        """Print detailed environment information"""
        print("🔍 DETAILED ENVIRONMENT ANALYSIS")
        print("=" * 60)

        print(f"🕐 Timestamp: {datetime.now().isoformat()}")
        print(f"🐍 Python: {sys.version}")
        print(f"📁 Working Directory: {os.getcwd()}")
        print(f"👤 User: {os.getenv('USER', 'unknown')}")
        print(f"🏠 Home: {os.getenv('HOME', 'unknown')}")
        print(f"🌐 Hostname: {os.getenv('HOSTNAME', 'unknown')}")

        # Network environment
        print(f"\n🌐 NETWORK ENVIRONMENT:")
        print(f"   GANCIO_BASE_URL: {self.base_url}")
        print(f"   GANCIO_EMAIL: {self.email}")
        print(f"   GANCIO_PASSWORD: {'[SET]' if self.password else '[NOT SET]'}")

        # Python packages
        print(f"\n📦 PYTHON PACKAGES:")
        try:
            import pkg_resources

            installed_packages = [
                d.project_name + "==" + d.version for d in pkg_resources.working_set
            ]
            relevant_packages = [
                pkg
                for pkg in installed_packages
                if any(
                    name in pkg.lower()
                    for name in ["requests", "urllib", "http", "ssl"]
                )
            ]
            for pkg in relevant_packages:
                print(f"   ✅ {pkg}")
        except:
            print("   ❌ Could not enumerate packages")

    def test_basic_connectivity(self):
        """Test basic network connectivity"""
        print(f"\n🔍 BASIC CONNECTIVITY TESTS")
        print("=" * 60)

        # Parse URL
        try:
            from urllib.parse import urlparse

            parsed = urlparse(self.base_url)
            host = parsed.hostname
            port = parsed.port or (80 if parsed.scheme == "http" else 443)

            print(f"🎯 Target: {host}:{port}")
            print(f"📡 Scheme: {parsed.scheme}")

        except Exception as e:
            print(f"❌ URL parsing error: {e}")
            return False

        # Test basic HTTP connectivity
        test_urls = [
            f"{self.base_url}/",
            f"{self.base_url}/api",
            f"{self.base_url}/api/events",
            f"{self.base_url}/login",
        ]

        connectivity_results = {}

        for url in test_urls:
            print(f"\n🧪 Testing: {url}")
            try:
                start_time = time.time()
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=False
                )
                end_time = time.time()

                print(f"   Status: {response.status_code}")
                print(f"   Time: {end_time - start_time:.2f}s")
                print(f"   Size: {len(response.content)} bytes")

                # Check for redirects
                if response.status_code in [301, 302, 303, 307, 308]:
                    print(
                        f"   Redirect to: {response.headers.get('location', 'unknown')}"
                    )

                connectivity_results[url] = {
                    "status": response.status_code,
                    "time": end_time - start_time,
                    "success": response.status_code < 400,
                }

            except requests.exceptions.ConnectTimeout:
                print(f"   ❌ Connection timeout")
                connectivity_results[url] = {"success": False, "error": "timeout"}
            except requests.exceptions.ConnectionError as e:
                print(f"   ❌ Connection error: {e}")
                connectivity_results[url] = {"success": False, "error": str(e)}
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                connectivity_results[url] = {"success": False, "error": str(e)}

        return connectivity_results

    def test_api_endpoints(self):
        """Test specific API endpoints"""
        print(f"\n🔍 API ENDPOINT TESTS")
        print("=" * 60)

        api_endpoints = [
            ("/api/events", "GET", "Events list"),
            ("/api/auth/me", "GET", "Auth status"),
            ("/auth/login", "GET", "Login page"),
        ]

        for endpoint, method, description in api_endpoints:
            url = f"{self.base_url}{endpoint}"
            print(f"\n🧪 {description}: {method} {endpoint}")

            try:
                if method == "GET":
                    response = self.session.get(url, timeout=self.timeout)

                print(f"   Status: {response.status_code}")
                print(
                    f"   Content-Type: {response.headers.get('content-type', 'unknown')}"
                )

                # Try to parse response
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    try:
                        json_data = response.json()
                        if endpoint == "/api/events" and isinstance(json_data, list):
                            print(f"   Events count: {len(json_data)}")
                        else:
                            print(
                                f"   JSON keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'not a dict'}"
                            )
                    except:
                        print(f"   JSON parsing failed")
                else:
                    print(f"   Content preview: {response.text[:100]}...")

            except Exception as e:
                print(f"   ❌ Error: {e}")

    def test_authentication_flow(self):
        """Test the complete authentication flow"""
        print(f"\n🔍 AUTHENTICATION FLOW TEST")
        print("=" * 60)

        if not self.email or not self.password:
            print("❌ Missing credentials - skipping auth test")
            return False

        print(f"🔐 Testing authentication for: {self.email}")

        # Step 1: Get login page
        print(f"\n1️⃣ Getting login page...")
        try:
            login_page_response = self.session.get(
                f"{self.base_url}/login", timeout=self.timeout
            )
            print(f"   Status: {login_page_response.status_code}")

            if login_page_response.status_code != 200:
                print(f"   ❌ Login page not accessible")
                return False

            # Check for CSRF tokens or other form data
            if "csrf" in login_page_response.text.lower():
                print(f"   🔒 CSRF protection detected")

            print(f"   ✅ Login page accessible")

        except Exception as e:
            print(f"   ❌ Login page error: {e}")
            return False

        # Step 2: Attempt login
        print(f"\n2️⃣ Attempting login...")
        login_data = {"email": self.email, "password": self.password}

        # Try different content types
        content_types = [
            ("application/x-www-form-urlencoded", "data"),
            ("application/json", "json"),
        ]

        login_success = False

        for content_type, param_type in content_types:
            print(f"   🧪 Trying {content_type}...")

            try:
                headers = {"Content-Type": content_type}

                if param_type == "json":
                    response = self.session.post(
                        f"{self.base_url}/auth/login",
                        json=login_data,
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}/auth/login",
                        data=login_data,
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )

                print(f"      Status: {response.status_code}")
                print(f"      Final URL: {response.url}")

                # Check for success indicators
                if "admin" in response.url.lower():
                    print(f"      ✅ Redirected to admin - SUCCESS!")
                    login_success = True
                    break
                elif (
                    response.status_code == 200 and "dashboard" in response.text.lower()
                ):
                    print(f"      ✅ Dashboard content detected - SUCCESS!")
                    login_success = True
                    break
                elif response.status_code in [200, 201]:
                    print(f"      ⚠️ Success status but unclear redirect")
                else:
                    print(f"      ❌ Login failed")

                # Show response preview
                print(f"      Response preview: {response.text[:200]}...")

            except Exception as e:
                print(f"      ❌ Login attempt error: {e}")

        # Step 3: Test authenticated access
        if login_success:
            print(f"\n3️⃣ Testing authenticated access...")
            try:
                auth_test_response = self.session.get(
                    f"{self.base_url}/api/events", timeout=self.timeout
                )
                print(f"   Status: {auth_test_response.status_code}")

                if auth_test_response.status_code == 200:
                    events = auth_test_response.json()
                    print(f"   ✅ Authenticated API access successful")
                    print(f"   📊 Events accessible: {len(events)}")
                else:
                    print(f"   ⚠️ API access status: {auth_test_response.status_code}")

            except Exception as e:
                print(f"   ❌ Authenticated access test error: {e}")

        return login_success

    def test_comprehensive_monitoring_compatibility(self):
        """Test if the monitoring system will work"""
        print(f"\n🔍 MONITORING SYSTEM COMPATIBILITY")
        print("=" * 60)

        try:
            # Test the same call the monitoring system makes
            response = self.session.get(
                f"{self.base_url}/api/events", timeout=self.timeout
            )

            print(f"📡 GET {self.base_url}/api/events")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                events = response.json()
                print(f"   ✅ Monitoring system should work")
                print(f"   📊 Events: {len(events)}")

                # Test event structure
                if events and len(events) > 0:
                    sample_event = events[0]
                    required_fields = ["id", "title", "start_datetime", "place"]
                    missing_fields = [
                        field for field in required_fields if field not in sample_event
                    ]

                    if missing_fields:
                        print(f"   ⚠️ Missing fields in events: {missing_fields}")
                    else:
                        print(f"   ✅ Event structure is compatible")

                return True
            else:
                print(
                    f"   ❌ Monitoring system will fail with status {response.status_code}"
                )
                print(f"   Response: {response.text[:200]}...")
                return False

        except Exception as e:
            print(f"   ❌ Monitoring compatibility test failed: {e}")
            return False

    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("🚀 ADVANCED GITHUB ACTIONS GANCIO DIAGNOSTICS")
        print("=" * 80)

        # Environment analysis
        self.print_environment_details()

        # Connectivity tests
        connectivity_ok = self.test_basic_connectivity()

        # API endpoint tests
        self.test_api_endpoints()

        # Authentication tests
        auth_ok = self.test_authentication_flow()

        # Monitoring compatibility
        monitoring_ok = self.test_comprehensive_monitoring_compatibility()

        # Summary
        print(f"\n📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)

        api_connectivity = any(
            result.get("success", False) for result in connectivity_ok.values()
        )

        print(f"🌐 Basic Connectivity: {'✅ PASS' if api_connectivity else '❌ FAIL'}")
        print(f"🔐 Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
        print(f"📊 Monitoring Compatible: {'✅ PASS' if monitoring_ok else '❌ FAIL'}")

        if api_connectivity and auth_ok and monitoring_ok:
            print(f"\n🎉 ALL TESTS PASSED - GitHub Actions should work!")
            return 0
        else:
            print(f"\n⚠️ SOME TESTS FAILED - Check details above")

            # Specific recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            if not api_connectivity:
                print(f"   🔧 Check Gancio service status and network configuration")
            if not auth_ok:
                print(f"   🔧 Verify GANCIO_EMAIL and GANCIO_PASSWORD secrets")
            if not monitoring_ok:
                print(f"   🔧 Check Gancio API permissions and response format")

            return 1


def main():
    debugger = AdvancedGancioDebugger()
    return debugger.run_full_diagnostic()


if __name__ == "__main__":
    sys.exit(main())
