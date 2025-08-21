# GitHub Actions Gancio Sync Troubleshooting Guide

## 🚀 Running the Simple Gancio Diagnostic Workflow

### Manual Trigger Steps

1. **Navigate to GitHub Actions**
   - Go to your repository on GitHub
   - Click on the "Actions" tab
   - Find "Simple Gancio Diagnostic" in the workflow list

2. **Trigger the Workflow**
   - Click on "Simple Gancio Diagnostic"
   - Click "Run workflow" (green button on the right)
   - Select the test type:
     - `connectivity` - Basic network and API tests
     - `authentication` - Login and session tests  
     - `full` - Complete diagnostic including monitoring system
   - Click "Run workflow"

3. **Monitor Execution**
   - The workflow will appear in the runs list
   - Click on the run to see detailed logs
   - Expand each step to see specific output

### Quick Trigger via CLI (Alternative)
```bash
# Using GitHub CLI (if installed)
gh workflow run "Simple Gancio Diagnostic" --field test_type=connectivity
gh workflow run "Simple Gancio Diagnostic" --field test_type=full
```

## 🔍 Diagnostic Output Interpretation

### ✅ Successful Output Patterns

```
🔍 Environment Diagnostics:
Runner: your-runner-hostname
✅ Localhost ping OK
✅ Port 13120 is listening  
✅ Gancio API accessible
📊 Events in Gancio: 42

🚀 ADVANCED GITHUB ACTIONS GANCIO DIAGNOSTICS
🌐 Basic Connectivity: ✅ PASS
🔐 Authentication: ✅ PASS
📊 Monitoring Compatible: ✅ PASS
🎉 ALL TESTS PASSED - GitHub Actions should work!
```

### ❌ Connection Issue Patterns

```
❌ Localhost ping failed
❌ Port 13120 not found
❌ Gancio API not accessible

🔍 BASIC CONNECTIVITY TESTS
🧪 Testing: http://localhost:13120/api/events
   ❌ Connection error: [Errno 111] Connection refused
```

**This indicates**: Gancio service is not running or not accessible on the expected port.

### 🔐 Authentication Issue Patterns

```
✅ Port 13120 is listening
✅ Gancio API accessible
🔐 Authentication: ❌ FAIL

🔍 AUTHENTICATION FLOW TEST
❌ Authentication failed
Response preview: {"error": "Invalid credentials"}
```

**This indicates**: Network connectivity is fine, but login credentials are incorrect or expired.

### ⚠️ Mixed Issue Patterns

```
✅ Gancio API accessible  
📊 Events in Gancio: unknown
⚠️ API access status: 401
```

**This indicates**: Basic connectivity works but API requires authentication for full access.

## 🛠️ Troubleshooting Commands by Issue Type

### Connection Issues (Port/Network)

1. **Check Gancio Service Status**
```bash
# SSH to your server
sudo systemctl status gancio
# or if using Docker
docker ps | grep gancio
docker logs gancio_container_name
```

2. **Verify Port Accessibility**
```bash
# On the server
netstat -tlnp | grep 13120
ss -tlnp | grep 13120

# From the runner
telnet your-server-ip 13120
nc -zv your-server-ip 13120
```

3. **Check Firewall Rules**
```bash
# Ubuntu/Debian
sudo ufw status
sudo iptables -L | grep 13120

# CentOS/RHEL  
sudo firewall-cmd --list-all
```

4. **Test Local Connectivity**
```bash
# Run the quick connectivity test
export GANCIO_BASE_URL="http://your-server:13120"
./scripts/event-sync/quick_connectivity_test.sh
```

### Authentication Issues

1. **Verify Secrets in GitHub**
   - Go to Settings → Secrets and variables → Actions
   - Ensure these secrets exist and are correctly set:
     - `GANCIO_BASE_URL`
     - `GANCIO_EMAIL` 
     - `GANCIO_PASSWORD`

2. **Test Credentials Manually**
```bash
# SSH to your runner and test
export GANCIO_BASE_URL="http://your-server:13120"
export GANCIO_EMAIL="your-email@example.com"  
export GANCIO_PASSWORD="your-password"

python3 -c "
import requests
session = requests.Session()
response = session.post('$GANCIO_BASE_URL/auth/login', 
                       data={'email': '$GANCIO_EMAIL', 'password': '$GANCIO_PASSWORD'})
print(f'Status: {response.status_code}')
print(f'URL: {response.url}')
"
```

3. **Check Gancio User Account**
   - Log into Gancio web interface manually
   - Verify the account exists and has admin privileges
   - Try resetting the password if needed

### Environment Issues

1. **Python Environment Problems**
```bash
# Check Python and packages
python3 --version
python3 -c "import requests; print('requests OK')"
python3 -c "import json; print('json OK')"

# Recreate virtual environment  
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip requests beautifulsoup4 lxml
```

2. **File Permission Issues**
```bash
# Check script permissions
ls -la scripts/event-sync/
chmod +x scripts/event-sync/*.py
chmod +x scripts/event-sync/*.sh
```

## 🔧 Debug Mode Configuration

### Enable Debug Mode in Workflows

1. **Add Debug Environment Variable**
Add this to your workflow's `env` section:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  RUNNER_DEBUG: 1
  GANCIO_DEBUG: true
```

2. **Enable Verbose Logging in Python Scripts**
Modify your sync script calls:
```yaml
- name: Run Sync with Debug
  run: |
    python3 enhanced_sync_with_complete_validation.py --verbose --debug
```

3. **Add Debug Output Steps**
```yaml  
- name: Debug Environment
  run: |
    echo "🔍 Debug Information:"
    env | grep -E "(GANCIO|PYTHON|PATH)" | sort
    echo "Working directory contents:"
    ls -la
    echo "Python packages:"
    pip list | grep -E "(requests|beautifulsoup|lxml)"
```

### Enhanced Debug Workflow Trigger

Create a debug version of your main workflow:
```yaml
name: Debug Event Sync
on:
  workflow_dispatch:
    inputs:
      debug_level:
        description: 'Debug level (1-3)'
        required: true
        default: '2'
        
env:
  ACTIONS_STEP_DEBUG: true
  RUNNER_DEBUG: 1
  GANCIO_DEBUG: ${{ github.event.inputs.debug_level }}
```

## 📊 Workflow Modification for Detailed Logs

### Add Pre-Sync Validation Steps

```yaml
- name: Pre-Sync Validation
  run: |
    echo "🔍 Pre-sync validation:"
    
    # Test all requirements
    python3 -c "import requests, json; print('✅ Python modules OK')"
    
    # Test Gancio connectivity
    curl -f "$GANCIO_BASE_URL/api/events" > /tmp/events.json
    EVENT_COUNT=$(cat /tmp/events.json | jq length)
    echo "📊 Current events: $EVENT_COUNT"
    
    # Test authentication
    python3 scripts/event-sync/advanced_github_actions_debug.py
    
    echo "✅ Pre-sync validation complete"
```

### Add Post-Sync Reporting

```yaml
- name: Post-Sync Reporting  
  if: always()
  run: |
    echo "📊 Sync Results Summary:"
    
    # Check final event count
    FINAL_COUNT=$(curl -s "$GANCIO_BASE_URL/api/events" | jq length 2>/dev/null || echo "unknown")
    echo "📊 Final event count: $FINAL_COUNT"
    
    # Check for any errors in logs
    if [ -f sync.log ]; then
      echo "⚠️ Sync log errors:"
      grep -i error sync.log || echo "No errors found"
    fi
    
    echo "✅ Post-sync reporting complete"
```

## 🔐 GitHub Actions Secrets Best Practices

### Required Secrets Configuration

1. **Navigate to Repository Settings**
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"

2. **Required Secrets**
```
GANCIO_BASE_URL=http://your-server:13120
GANCIO_EMAIL=admin@yourdomain.com
GANCIO_PASSWORD=your-secure-password
```

3. **Optional Secrets for Enhanced Features**
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
MONITORING_SLACK_WEBHOOK=https://hooks.slack.com/...
```

### Security Best Practices

1. **Use Specific Service Accounts**
   - Create dedicated Gancio user account for sync
   - Grant minimal required permissions
   - Use strong, unique passwords

2. **Regular Secret Rotation**
   - Update passwords monthly
   - Update secrets in GitHub immediately after changing passwords
   - Test workflows after secret updates

3. **Environment-Specific Secrets**
   - Use different secrets for staging vs production
   - Consider using GitHub Environments for additional security
   - Implement approval requirements for production deployments

4. **Secret Validation**
```yaml
- name: Validate Secrets
  run: |
    echo "🔍 Secret validation:"
    [ -n "$GANCIO_BASE_URL" ] && echo "✅ GANCIO_BASE_URL set" || echo "❌ GANCIO_BASE_URL missing"
    [ -n "$GANCIO_EMAIL" ] && echo "✅ GANCIO_EMAIL set" || echo "❌ GANCIO_EMAIL missing"  
    [ -n "$GANCIO_PASSWORD" ] && echo "✅ GANCIO_PASSWORD set" || echo "❌ GANCIO_PASSWORD missing"
```

### Dynamic URL Configuration

Support multiple environments:
```yaml
env:
  GANCIO_BASE_URL: ${{ 
    github.ref == 'refs/heads/main' && secrets.GANCIO_PROD_URL || 
    github.ref == 'refs/heads/staging' && secrets.GANCIO_STAGING_URL || 
    secrets.GANCIO_DEV_URL 
  }}
```

## 🎯 Quick Workflow Health Check

Run this command to verify your workflow setup:
```bash
# Check workflow files
find .github/workflows -name "*.yml" -exec echo "=== {} ===" \; -exec head -20 {} \;

# Verify diagnostic scripts exist
ls -la scripts/event-sync/github_actions_diagnostics.py
ls -la scripts/event-sync/quick_connectivity_test.sh
ls -la scripts/event-sync/advanced_github_actions_debug.py
```

## 📞 Emergency Troubleshooting Checklist

If workflows are completely failing:

1. ✅ **Check GitHub Actions Service Status**
   - Visit https://www.githubstatus.com/

2. ✅ **Verify Self-Hosted Runner Status**  
   - Settings → Actions → Runners
   - Ensure runner shows "Online"

3. ✅ **Test Basic Runner Connectivity**
```bash
# SSH to runner
curl -I https://api.github.com
python3 --version
docker --version (if needed)
```

4. ✅ **Run Local Diagnostic**
```bash
export GANCIO_BASE_URL="http://your-server:13120"
export GANCIO_EMAIL="your-email"
export GANCIO_PASSWORD="your-password"
./scripts/event-sync/quick_connectivity_test.sh
```

5. ✅ **Check Gancio Service**
```bash
# On your server
sudo systemctl status gancio
curl -I http://localhost:13120/api/events
```

This guide should help you quickly identify and resolve most GitHub Actions workflow issues with your Gancio sync system.
