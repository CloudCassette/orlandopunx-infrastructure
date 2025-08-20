# GitHub Actions Troubleshooting Guide

## 🚨 Common Issues Identified

Based on your failing GitHub Actions run, here are the most likely causes and solutions:

### 1. **Gancio API Connectivity Issues**
The 404 error suggests the monitoring script cannot reach your Gancio instance.

**Possible Causes:**
- Gancio not running on the self-hosted runner
- Different IP/port binding in GitHub Actions environment
- Firewall or network configuration issues
- Wrong GANCIO_BASE_URL setting

### 2. **Missing Environment Variables**
The script may not be receiving the correct Gancio credentials or URL.

### 3. **Python Dependencies**
Missing or incorrectly installed Python packages.

## 🔧 Fixes Implemented

### 1. **Updated Workflow** (`.github/workflows/sync-with-validation-fixed.yml`)
- ✅ Added configurable GANCIO_BASE_URL environment variable
- ✅ Enhanced Python environment setup with proper dependency management
- ✅ Added comprehensive connectivity testing before sync
- ✅ Added debug mode with detailed diagnostics
- ✅ Improved error handling and logging
- ✅ Added authentication testing

### 2. **Diagnostic Tools**
- ✅ `github_actions_diagnostics.py` - Comprehensive connectivity and auth testing
- ✅ `simple-diagnostic.yml` - Minimal workflow for testing
- ✅ Updated monitoring system to use environment variables

### 3. **Environment Variable Configuration**
```yaml
env:
  GANCIO_EMAIL: ${{ secrets.GANCIO_EMAIL }}
  GANCIO_PASSWORD: ${{ secrets.GANCIO_PASSWORD }}
  GANCIO_BASE_URL: ${{ secrets.GANCIO_BASE_URL || 'http://localhost:13120' }}
```

## 🛠️ Required GitHub Secrets

You need to set these secrets in your repository:

1. **GANCIO_EMAIL** - Your Gancio admin email
2. **GANCIO_PASSWORD** - Your Gancio admin password  
3. **GANCIO_BASE_URL** - The URL to your Gancio instance (if different from localhost:13120)

### Setting Secrets:
1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with the exact names above

## 🧪 Testing Commands

### Local Testing (run these on your self-hosted runner):

```bash
# 1. Test basic Gancio connectivity
curl -f -s http://localhost:13120/api/events > /dev/null && echo "✅ Gancio accessible" || echo "❌ Gancio not accessible"

# 2. Check Gancio event count
curl -s http://localhost:13120/api/events | jq length

# 3. Test authentication (replace with your credentials)
export GANCIO_EMAIL="your-email@example.com"
export GANCIO_PASSWORD="your-password"
cd scripts/event-sync
python3 github_actions_diagnostics.py

# 4. Test monitoring system
python3 comprehensive_monitoring_system.py --ci-mode

# 5. Check if Gancio is running
netstat -tlnp | grep :13120
ps aux | grep gancio

# 6. Check runner environment
echo "Runner: $(hostname)"
echo "User: $(whoami)"
echo "Working Dir: $(pwd)"
```

### GitHub Actions Testing:

1. **Run Simple Diagnostic** (recommended first step):
   - Go to Actions → Simple Gancio Diagnostic → Run workflow
   - This will test connectivity and authentication

2. **Run Fixed Workflow with Debug**:
   - Go to Actions → Enhanced Event Sync with Validation (Fixed) → Run workflow
   - Set "debug_mode" to true
   - This will show detailed diagnostics

## 🔍 Minimal Working Example

Here's a minimal GitHub Actions step that should work:

```yaml
- name: Test Gancio Connection
  env:
    GANCIO_EMAIL: ${{ secrets.GANCIO_EMAIL }}
    GANCIO_PASSWORD: ${{ secrets.GANCIO_PASSWORD }}
    GANCIO_BASE_URL: ${{ secrets.GANCIO_BASE_URL || 'http://localhost:13120' }}
  run: |
    # Set up Python
    python3 -m venv venv
    source venv/bin/activate
    pip install requests
    
    # Test basic connectivity
    python3 -c "
import requests
import os

base_url = os.getenv('GANCIO_BASE_URL', 'http://localhost:13120')
print(f'Testing: {base_url}/api/events')

try:
    response = requests.get(f'{base_url}/api/events', timeout=10)
    if response.status_code == 200:
        events = response.json()
        print(f'✅ SUCCESS: Found {len(events)} events')
    else:
        print(f'❌ FAILED: Status {response.status_code}')
except Exception as e:
    print(f'❌ ERROR: {e}')
"
```

## 🎯 Step-by-Step Resolution

### Step 1: Verify Gancio is Running
```bash
# On your self-hosted runner machine:
sudo systemctl status gancio
# or
ps aux | grep gancio
netstat -tlnp | grep :13120
```

### Step 2: Test Local Connectivity
```bash
curl -f http://localhost:13120/api/events
```

### Step 3: Set GitHub Secrets
- Add GANCIO_EMAIL, GANCIO_PASSWORD, and GANCIO_BASE_URL secrets

### Step 4: Run Diagnostic Workflow
- Use the "Simple Gancio Diagnostic" workflow first

### Step 5: Fix Based on Results
- If connectivity fails: Check Gancio service and network
- If authentication fails: Verify credentials and login endpoint
- If all works: Use the fixed main workflow

## 🚀 Quick Fix Commands

Run these to immediately test and fix:

```bash
# 1. Make scripts executable
chmod +x scripts/event-sync/*.py

# 2. Test the diagnostic script locally
cd scripts/event-sync
export GANCIO_EMAIL="your-email"
export GANCIO_PASSWORD="your-password" 
export GANCIO_BASE_URL="http://localhost:13120"
python3 github_actions_diagnostics.py

# 3. Commit the fixed workflows
git add .github/workflows/sync-with-validation-fixed.yml
git add .github/workflows/simple-diagnostic.yml  
git add scripts/event-sync/github_actions_diagnostics.py
git commit -m "fix: Add GitHub Actions diagnostics and improved workflows"
git push origin main
```

## 📊 Expected Results

After implementing these fixes:
- ✅ Connectivity test should pass
- ✅ Authentication should work
- ✅ Monitoring system should run without 404 errors
- ✅ Sync workflow should complete successfully

## 🆘 If Issues Persist

If you're still having problems:

1. **Check Gancio Logs**: Look at Gancio application logs for errors
2. **Network Configuration**: Verify firewall and port settings
3. **Runner Environment**: Ensure the self-hosted runner has proper access
4. **Try Alternative URLs**: Test if Gancio is accessible via different URLs (IP, hostname, etc.)

The diagnostic workflows will provide detailed information to help identify the exact issue.
