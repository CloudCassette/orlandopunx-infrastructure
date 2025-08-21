#!/usr/bin/env python3
"""
GitHub Actions Secrets Validation Script
Validates that all required secrets are properly configured
"""

import os
import sys
from urllib.parse import urlparse

import requests


def validate_secrets():
    """Validate all required GitHub Actions secrets"""
    print("🔐 GITHUB ACTIONS SECRETS VALIDATION")
    print("=" * 50)

    secrets_status = {}

    # Required secrets
    required_secrets = {
        "GANCIO_BASE_URL": "Gancio server URL",
        "GANCIO_EMAIL": "Admin email for authentication",
        "GANCIO_PASSWORD": "Admin password for authentication",
    }

    # Check if secrets are set
    print("\n📋 CHECKING SECRET AVAILABILITY:")
    all_secrets_present = True

    for secret_name, description in required_secrets.items():
        value = os.getenv(secret_name)
        if value:
            print(f"   ✅ {secret_name}: {description} - [SET]")
            secrets_status[secret_name] = {"present": True, "value": value}
        else:
            print(f"   ❌ {secret_name}: {description} - [NOT SET]")
            secrets_status[secret_name] = {"present": False, "value": None}
            all_secrets_present = False

    if not all_secrets_present:
        print("\n❌ MISSING SECRETS DETECTED")
        print("Please configure the missing secrets in GitHub Actions:")
        print("Repository → Settings → Secrets and variables → Actions")
        return False

    # Validate secret formats
    print("\n🔍 VALIDATING SECRET FORMATS:")

    # Validate GANCIO_BASE_URL
    base_url = secrets_status["GANCIO_BASE_URL"]["value"]
    try:
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            print(f"   ❌ GANCIO_BASE_URL: Invalid URL format")
            return False
        else:
            print(
                f"   ✅ GANCIO_BASE_URL: Valid URL format ({parsed_url.scheme}://{parsed_url.netloc})"
            )

            # Extract host and port for connectivity test
            host = parsed_url.hostname
            port = parsed_url.port or (80 if parsed_url.scheme == "http" else 443)
            print(f"      → Host: {host}, Port: {port}")

    except Exception as e:
        print(f"   ❌ GANCIO_BASE_URL: Error parsing URL - {e}")
        return False

    # Validate GANCIO_EMAIL
    email = secrets_status["GANCIO_EMAIL"]["value"]
    if "@" in email and "." in email.split("@")[1]:
        print(f"   ✅ GANCIO_EMAIL: Valid email format")
    else:
        print(f"   ❌ GANCIO_EMAIL: Invalid email format")
        return False

    # Validate GANCIO_PASSWORD
    password = secrets_status["GANCIO_PASSWORD"]["value"]
    if len(password) >= 8:
        print(f"   ✅ GANCIO_PASSWORD: Adequate length ({len(password)} chars)")
    else:
        print(
            f"   ⚠️ GANCIO_PASSWORD: Short password ({len(password)} chars) - consider using a longer password"
        )

    # Test connectivity with secrets
    print("\n🌐 TESTING CONNECTIVITY WITH SECRETS:")

    try:
        # Test basic connectivity
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   ✅ Basic connectivity: {response.status_code}")

        # Test API endpoint
        api_response = requests.get(f"{base_url}/api/events", timeout=10)
        print(f"   ✅ API endpoint: {api_response.status_code}")

        if api_response.status_code == 200:
            events = api_response.json()
            print(f"      → Events available: {len(events)}")

    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed: Cannot reach {base_url}")
        print("      → Check if Gancio service is running")
        print("      → Verify firewall/network configuration")
        return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Connection timeout: {base_url} not responding")
        return False
    except Exception as e:
        print(f"   ❌ Connectivity error: {e}")
        return False

    # Test authentication with secrets
    print("\n🔐 TESTING AUTHENTICATION WITH SECRETS:")

    try:
        session = requests.Session()

        # Get login page
        login_response = session.get(f"{base_url}/login", timeout=10)
        if login_response.status_code != 200:
            print(f"   ❌ Login page not accessible: {login_response.status_code}")
            return False

        # Attempt authentication
        auth_response = session.post(
            f"{base_url}/auth/login",
            data={"email": email, "password": password},
            timeout=10,
            allow_redirects=True,
        )

        print(f"   Authentication response: {auth_response.status_code}")
        print(f"   Final URL: {auth_response.url}")

        if "admin" in auth_response.url.lower():
            print(f"   ✅ Authentication successful - redirected to admin")

            # Test authenticated API access
            api_auth_response = session.get(f"{base_url}/api/events", timeout=10)
            if api_auth_response.status_code == 200:
                print(f"   ✅ Authenticated API access successful")
            else:
                print(
                    f"   ⚠️ Authenticated API access: {api_auth_response.status_code}"
                )

            return True
        else:
            print(f"   ❌ Authentication failed - not redirected to admin")
            print(f"   Response preview: {auth_response.text[:200]}...")
            return False

    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False

    return True


def print_secret_setup_guide():
    """Print guide for setting up secrets in GitHub"""
    print("\n📖 GITHUB SECRETS SETUP GUIDE")
    print("=" * 50)
    print("1. Go to your GitHub repository")
    print("2. Click Settings → Secrets and variables → Actions")
    print("3. Click 'New repository secret'")
    print("4. Add these secrets:")
    print()
    print("   GANCIO_BASE_URL")
    print("   └── Example: http://your-server.com:13120")
    print("   └── Example: https://gancio.yourdomain.com")
    print()
    print("   GANCIO_EMAIL")
    print("   └── Example: admin@yourdomain.com")
    print("   └── Must be a valid Gancio admin account")
    print()
    print("   GANCIO_PASSWORD")
    print("   └── The password for the admin account")
    print("   └── Use a strong, unique password")
    print()
    print("5. Test the secrets by running the diagnostic workflow")


def main():
    """Main validation function"""
    print("🚀 Starting GitHub Actions secrets validation...")

    if validate_secrets():
        print("\n🎉 ALL SECRETS VALIDATED SUCCESSFULLY!")
        print("✅ Your GitHub Actions workflow should work correctly")
        return 0
    else:
        print("\n❌ SECRETS VALIDATION FAILED")
        print("⚠️ Your GitHub Actions workflow will likely fail")
        print_secret_setup_guide()
        return 1


if __name__ == "__main__":
    sys.exit(main())
