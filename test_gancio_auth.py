#!/usr/bin/env python3

import requests

BASE_URL = "https://orlandopunx.com"
EMAIL = "admin"
PASSWORD = "OrlandoPunkShows2024!"

# Test different authentication endpoints
endpoints = [
    "/api/auth/local",
    "/api/auth/login",
    "/api/login",
    "/auth/login",
    "/api/user/login",
    "/api/auth",
]

print("Testing Gancio authentication endpoints...")
print("=" * 50)

for endpoint in endpoints:
    url = BASE_URL + endpoint
    print(f"\nTrying: {url}")

    # Try different payload formats
    payloads = [
        {"email": EMAIL, "password": PASSWORD},
        {"username": EMAIL, "password": PASSWORD},
        {"identifier": EMAIL, "password": PASSWORD},
    ]

    for payload in payloads:
        try:
            response = requests.post(url, json=payload, timeout=5)
            print(f"  Payload: {list(payload.keys())}")
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✅ SUCCESS! Response: {response.text[:100]}")
                data = response.json()
                if "token" in data or "jwt" in data or "accessToken" in data:
                    print(f"  🔑 Token found!")
                break
            elif response.status_code != 404:
                print(f"  Response: {response.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")

# Also test if we can access events without auth
print("\n\nTesting event endpoints without auth...")
event_endpoints = ["/api/events", "/api/event", "/api/events/unconfirmed"]

for endpoint in event_endpoints:
    url = BASE_URL + endpoint
    print(f"\nTrying GET {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = (
                response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else None
            )
            if data:
                print(
                    f"  ✅ Got data! Type: {type(data)}, Length: {len(data) if isinstance(data, list) else 'N/A'}"
                )
    except Exception as e:
        print(f"  Error: {e}")
