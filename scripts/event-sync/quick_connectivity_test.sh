#!/bin/bash

# Quick connectivity test for Gancio debugging
# Run this on your self-hosted runner to diagnose issues

set -e

echo "🔍 QUICK GANCIO CONNECTIVITY TEST"
echo "=================================="

# Check environment variables
echo "📋 Environment Variables:"
echo "GANCIO_BASE_URL: ${GANCIO_BASE_URL:-[NOT SET]}"
echo "GANCIO_EMAIL: ${GANCIO_EMAIL:-[NOT SET]}"
echo "GANCIO_PASSWORD: ${GANCIO_PASSWORD:+[SET]}"

if [ -z "$GANCIO_BASE_URL" ]; then
    echo "❌ GANCIO_BASE_URL not set"
    exit 1
fi

# Extract host and port
HOST=$(echo "$GANCIO_BASE_URL" | sed -E 's|https?://([^/:]+).*|\1|')
PORT=$(echo "$GANCIO_BASE_URL" | sed -E 's|.*:([0-9]+).*|\1|')

echo -e "\n🎯 Target Information:"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Full URL: $GANCIO_BASE_URL"

# Test network connectivity
echo -e "\n🌐 Network Connectivity Tests:"

echo "1. Testing ping to host..."
if ping -c 3 -W 5 "$HOST" > /dev/null 2>&1; then
    echo "   ✅ Ping successful"
else
    echo "   ⚠️ Ping failed (might be blocked)"
fi

echo "2. Testing port connectivity..."
if timeout 5 bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null; then
    echo "   ✅ Port $PORT is accessible"
else
    echo "   ❌ Port $PORT is not accessible"
fi

echo "3. Testing HTTP connectivity..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$GANCIO_BASE_URL/" || echo "000")
if [ "$HTTP_STATUS" -ne "000" ]; then
    echo "   ✅ HTTP response: $HTTP_STATUS"
else
    echo "   ❌ HTTP connection failed"
fi

echo "4. Testing API endpoint..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$GANCIO_BASE_URL/api/events" || echo "000")
if [ "$API_STATUS" -ne "000" ]; then
    echo "   ✅ API response: $API_STATUS"
else
    echo "   ❌ API connection failed"
fi

# Check for running services
echo -e "\n🔧 Service Status:"

echo "1. Docker containers:"
if command -v docker > /dev/null 2>&1; then
    GANCIO_CONTAINERS=$(docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -i gancio || echo "None found")
    echo "   $GANCIO_CONTAINERS"
else
    echo "   Docker not available"
fi

echo "2. Listening ports:"
LISTENING_PORTS=$(netstat -tlnp 2>/dev/null | grep -E "(13120|3000|8080)" || echo "None found")
echo "   $LISTENING_PORTS"

echo "3. Gancio processes:"
GANCIO_PROCESSES=$(ps aux | grep -i gancio | grep -v grep || echo "None found")
echo "   $GANCIO_PROCESSES"

# Quick authentication test if credentials are available
if [ -n "$GANCIO_EMAIL" ] && [ -n "$GANCIO_PASSWORD" ]; then
    echo -e "\n🔐 Authentication Test:"
    
    # Create temporary Python script for auth test
    cat > /tmp/quick_auth_test.py << 'PYEOF'
import requests
import os
import sys

base_url = os.getenv('GANCIO_BASE_URL')
email = os.getenv('GANCIO_EMAIL')
password = os.getenv('GANCIO_PASSWORD')

session = requests.Session()

try:
    # Test login page
    login_resp = session.get(f'{base_url}/login', timeout=10)
    print(f'Login page: {login_resp.status_code}')
    
    # Test authentication
    auth_resp = session.post(
        f'{base_url}/auth/login',
        data={'email': email, 'password': password},
        timeout=10,
        allow_redirects=True
    )
    
    print(f'Auth response: {auth_resp.status_code}')
    print(f'Final URL: {auth_resp.url}')
    
    if 'admin' in auth_resp.url.lower():
        print('✅ Authentication successful')
        
        # Test API access
        api_resp = session.get(f'{base_url}/api/events', timeout=10)
        print(f'API access: {api_resp.status_code}')
        
        if api_resp.status_code == 200:
            events = api_resp.json()
            print(f'✅ Found {len(events)} events')
        else:
            print('❌ API access failed')
    else:
        print('❌ Authentication failed')
        
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
PYEOF
    
    if command -v python3 > /dev/null 2>&1; then
        python3 /tmp/quick_auth_test.py
        rm -f /tmp/quick_auth_test.py
    else
        echo "   Python3 not available for auth test"
    fi
else
    echo -e "\n⚠️ Credentials not available for authentication test"
fi

echo -e "\n📊 TEST COMPLETE"
echo "=================="
echo "Use the results above to identify connectivity issues."
echo "Common issues:"
echo "- Port not accessible: Check firewall/network rules"
echo "- HTTP connection failed: Check if Gancio service is running"
echo "- Authentication failed: Verify credentials and login endpoint"
