# GitHub Actions Failure Analysis Guide

## 🔍 How to Interpret GitHub Actions Failure Logs Efficiently

### **Step-by-Step Log Analysis Process**

1. **Navigate to the Failed Run**
   - Go to your repo → Actions tab → Click the failed run
   - Click on the job name (e.g., "diagnostic")
   - Look for red ❌ indicators next to step names

2. **Quick Failure Identification**
   - **Red steps** = Failed steps
   - **Yellow steps** = Warnings or skipped
   - **Green steps** = Successful steps
   - Look for the **first red step** - this is usually the root cause

3. **Expand Failed Steps**
   - Click on the failed step to expand the log
   - Look for these key error indicators:

### **Common Error Patterns & Solutions**

#### **🔴 Environment/Setup Errors**
```
Error: Unable to locate executable file: python3
/bin/bash: pip: command not found
```
**Root Cause:** Missing Python or pip installation
**Solution:** Add Python setup step or check runner configuration

#### **🔴 Network/Connectivity Errors**
```
curl: (7) Failed to connect to localhost port 13120
Connection refused
```
**Root Cause:** Gancio service not running or wrong URL
**Solution:** Check GANCIO_BASE_URL and service status

#### **🔴 Authentication Errors**
```
401 Unauthorized
Invalid credentials
```
**Root Cause:** Wrong GANCIO_EMAIL or GANCIO_PASSWORD
**Solution:** Verify secrets in GitHub settings

#### **🔴 Permission Errors**
```
Permission denied
bash: ./script.py: Permission denied
```
**Root Cause:** Script not executable
**Solution:** Add `chmod +x` step

#### **🔴 Python Import Errors**
```
ModuleNotFoundError: No module named 'requests'
ImportError: No module named 'bs4'
```
**Root Cause:** Missing Python packages
**Solution:** Check virtual environment and pip install steps

#### **🔴 File Not Found Errors**
```
FileNotFoundError: [Errno 2] No such file or directory
python3: can't open file 'missing_script.py'
```
**Root Cause:** Missing files or wrong working directory
**Solution:** Verify file paths and checkout step

### **Log Analysis Quick Commands**

To analyze logs more effectively, look for these patterns:

```bash
# Error indicators to search for in logs:
- "Error:"
- "Failed"
- "Exception"
- "Traceback"
- "exit code 1"
- "command not found"
- "Permission denied"
- "Connection refused"
```

## 🔧 Enable Detailed Debug Logging

### **Method 1: Repository-Level Debug Settings**

Add to your workflow file:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
  RUNNER_DEBUG: 1
```

### **Method 2: Enable Debug Mode via Secrets**

1. Go to **Repository Settings → Secrets and Variables → Actions**
2. Add these secrets:
```
ACTIONS_STEP_DEBUG=true
ACTIONS_RUNNER_DEBUG=true
```

3. Reference in workflow:
```yaml
env:
  ACTIONS_STEP_DEBUG: ${{ secrets.ACTIONS_STEP_DEBUG }}
  ACTIONS_RUNNER_DEBUG: ${{ secrets.ACTIONS_RUNNER_DEBUG }}
```

### **Method 3: Workflow-Specific Debug**

Add debug steps throughout your workflow:
```yaml
- name: Debug Step
  run: |
    echo "🔍 DEBUG INFO:"
    echo "Working Directory: $(pwd)"
    echo "User: $(whoami)"
    echo "Environment Variables:"
    env | sort
    echo "File System:"
    ls -la
    echo "Network Interfaces:"
    ip addr show | grep -E "inet|UP"
```

## 🏠 Local Debugging Strategies

### **Option 1: Using `act` (GitHub Actions Runner)**

Install and use `act` to run workflows locally:

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run your workflow locally
act workflow_dispatch -W .github/workflows/simple-diagnostic.yml

# Run with secrets file
echo "GANCIO_BASE_URL=http://localhost:13120" > .secrets
echo "GANCIO_EMAIL=admin@test.com" >> .secrets
echo "GANCIO_PASSWORD=password" >> .secrets
act workflow_dispatch -s .secrets -W .github/workflows/simple-diagnostic.yml

# Debug mode
act workflow_dispatch -v -W .github/workflows/simple-diagnostic.yml
```

### **Option 2: Direct Script Execution**

Test your scripts directly on the runner:

```bash
# SSH to your self-hosted runner
ssh user@your-runner-host

# Set up the same environment as the workflow
export GANCIO_BASE_URL="http://localhost:13120"
export GANCIO_EMAIL="admin@test.com" 
export GANCIO_PASSWORD="password"

# Create virtual environment like the workflow
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 lxml

# Run diagnostic scripts manually
cd /path/to/your/repo
python3 scripts/event-sync/advanced_github_actions_debug.py
```

### **Option 3: Using `tmate` for Interactive Debugging**

Add a tmate step to your workflow for live debugging:

```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
  if: failure() # Only run on failure
  with:
    limit-access-to-actor: true
```

This gives you an SSH session into the runner when the workflow fails.

## ✅ Environment Variables & Secrets Verification

### **Create Verification Steps**

Add these steps to your workflow:

```yaml
- name: Verify Environment Setup
  run: |
    echo "🔍 ENVIRONMENT VERIFICATION"
    echo "=========================="
    
    # Check system info
    echo "System: $(uname -a)"
    echo "User: $(whoami)"
    echo "Home: $HOME"
    echo "PWD: $(pwd)"
    echo "Shell: $SHELL"
    
    # Check Python
    echo -e "\n🐍 PYTHON ENVIRONMENT:"
    python3 --version 2>/dev/null && echo "✅ Python3 available" || echo "❌ Python3 missing"
    which python3 || echo "Python3 path not found"
    
    # Check PATH
    echo -e "\n📍 PATH:"
    echo $PATH | tr ':' '\n'
    
    # Check if running in container
    echo -e "\n🐳 CONTAINER CHECK:"
    [ -f /.dockerenv ] && echo "Running in Docker" || echo "Not in Docker"

- name: Verify Secrets Injection  
  run: |
    echo "🔐 SECRETS VERIFICATION"
    echo "======================"
    
    # Check if secrets are set (without revealing values)
    echo "GANCIO_BASE_URL: ${GANCIO_BASE_URL:+[SET]}"
    echo "GANCIO_EMAIL: ${GANCIO_EMAIL:+[SET]}"  
    echo "GANCIO_PASSWORD: ${GANCIO_PASSWORD:+[SET]}"
    
    # Validate URL format
    if [[ -n "$GANCIO_BASE_URL" ]]; then
      if [[ "$GANCIO_BASE_URL" =~ ^https?://[^/]+.*$ ]]; then
        echo "✅ GANCIO_BASE_URL format valid"
      else
        echo "❌ GANCIO_BASE_URL format invalid"
      fi
    else
      echo "❌ GANCIO_BASE_URL not set"
    fi
    
    # Validate email format
    if [[ -n "$GANCIO_EMAIL" ]]; then
      if [[ "$GANCIO_EMAIL" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
        echo "✅ GANCIO_EMAIL format valid"
      else
        echo "❌ GANCIO_EMAIL format invalid"
      fi
    else
      echo "❌ GANCIO_EMAIL not set"
    fi
```

## 📊 Resource & Environment Diagnostics

### **Comprehensive System Check Step**

```yaml
- name: System Resource Diagnostics
  run: |
    echo "💾 SYSTEM RESOURCE DIAGNOSTICS"
    echo "=============================="
    
    # Memory
    echo "🧠 Memory Usage:"
    free -h
    
    # Disk space  
    echo -e "\n💿 Disk Usage:"
    df -h
    
    # CPU info
    echo -e "\n🖥️ CPU Info:"
    nproc
    cat /proc/cpuinfo | grep "model name" | head -1
    
    # Load average
    echo -e "\n📈 System Load:"
    uptime
    
    # Network interfaces
    echo -e "\n🌐 Network Interfaces:"
    ip addr show | grep -E "inet|UP" || ifconfig | grep -E "inet|UP"
    
    # DNS resolution
    echo -e "\n🔍 DNS Test:"
    nslookup github.com || echo "DNS resolution failed"
    
    # Internet connectivity
    echo -e "\n🌍 Internet Test:"
    curl -s --max-time 5 https://api.github.com/zen || echo "Internet connectivity failed"
    
    # Running processes
    echo -e "\n🔄 Key Processes:"
    ps aux | head -10
    
    # Port listeners
    echo -e "\n🚪 Listening Ports:"
    netstat -tlnp | head -10 || ss -tlnp | head -10
```

### **Network Connectivity Deep Dive**

```yaml
- name: Network Connectivity Analysis
  run: |
    echo "🌐 NETWORK CONNECTIVITY ANALYSIS" 
    echo "================================"
    
    # Extract host from GANCIO_BASE_URL
    if [[ -n "$GANCIO_BASE_URL" ]]; then
      HOST=$(echo "$GANCIO_BASE_URL" | sed -E 's|https?://([^/:]+).*|\1|')
      PORT=$(echo "$GANCIO_BASE_URL" | sed -E 's|.*:([0-9]+).*|\1|' | head -1)
      
      echo "Target Host: $HOST"
      echo "Target Port: $PORT"
      
      # Test DNS resolution
      echo -e "\n🔍 DNS Resolution:"
      nslookup "$HOST" || echo "DNS lookup failed"
      
      # Test ping (if allowed)
      echo -e "\n📡 Ping Test:"
      ping -c 3 -W 3 "$HOST" || echo "Ping failed (may be blocked)"
      
      # Test port connectivity  
      echo -e "\n🚪 Port Test:"
      timeout 10 bash -c "</dev/tcp/$HOST/$PORT" && echo "✅ Port $PORT open" || echo "❌ Port $PORT closed/filtered"
      
      # Test HTTP connectivity
      echo -e "\n🌍 HTTP Test:"
      curl -I -s --max-time 10 "$GANCIO_BASE_URL" || echo "HTTP connection failed"
      
    else
      echo "❌ GANCIO_BASE_URL not set - skipping network tests"
    fi
```

## 🚀 Minimal Debug Workflow for Root Cause Analysis

Create a new workflow file: `.github/workflows/emergency-debug.yml`

```yaml
name: Emergency Debug Analysis

on:
  workflow_dispatch:
    inputs:
      debug_target:
        description: 'What to debug'
        required: true
        default: 'environment'
        type: choice
        options:
        - environment
        - network
        - secrets
        - scripts
        - full

jobs:
  emergency-debug:
    runs-on: self-hosted
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Emergency System Analysis
      run: |
        echo "🚨 EMERGENCY DEBUG ANALYSIS"
        echo "==========================="
        echo "Debug Target: ${{ github.event.inputs.debug_target }}"
        echo "Timestamp: $(date -Iseconds)"
        echo ""
        
        # Always check basics
        echo "🔍 BASIC SYSTEM INFO:"
        echo "Hostname: $(hostname)"
        echo "User: $(whoami)"
        echo "Working Directory: $(pwd)"
        echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
        echo "Shell: $SHELL"
        echo ""
        
    - name: Environment Debug
      if: github.event.inputs.debug_target == 'environment' || github.event.inputs.debug_target == 'full'
      run: |
        echo "🔍 ENVIRONMENT DEEP DIVE:"
        echo "PATH: $PATH"
        echo "HOME: $HOME"
        echo "USER: $USER"
        echo ""
        echo "Available commands:"
        which python3 pip3 curl git || echo "Some commands missing"
        echo ""
        echo "Repository files:"
        ls -la
        echo ""
        echo "Scripts directory:"
        ls -la scripts/event-sync/ || echo "Scripts directory missing"
        
    - name: Network Debug
      if: github.event.inputs.debug_target == 'network' || github.event.inputs.debug_target == 'full'
      run: |
        echo "🌐 NETWORK ANALYSIS:"
        echo "Interfaces:"
        ip addr show | grep -E "inet|UP" 2>/dev/null || ifconfig 2>/dev/null || echo "Network info unavailable"
        echo ""
        echo "Internet connectivity:"
        curl -s --max-time 5 https://api.github.com/zen && echo "✅ Internet OK" || echo "❌ Internet failed"
        echo ""
        echo "Listening ports:"
        netstat -tlnp 2>/dev/null | head -5 || ss -tlnp 2>/dev/null | head -5 || echo "Port info unavailable"
        
    - name: Secrets Debug
      if: github.event.inputs.debug_target == 'secrets' || github.event.inputs.debug_target == 'full'
      env:
        GANCIO_BASE_URL: ${{ secrets.GANCIO_BASE_URL }}
        GANCIO_EMAIL: ${{ secrets.GANCIO_EMAIL }}
        GANCIO_PASSWORD: ${{ secrets.GANCIO_PASSWORD }}
      run: |
        echo "🔐 SECRETS ANALYSIS:"
        echo "GANCIO_BASE_URL: ${GANCIO_BASE_URL:+[SET]} ${GANCIO_BASE_URL:-[NOT SET]}"
        echo "GANCIO_EMAIL: ${GANCIO_EMAIL:+[SET]} ${GANCIO_EMAIL:-[NOT SET]}"
        echo "GANCIO_PASSWORD: ${GANCIO_PASSWORD:+[SET]} ${GANCIO_PASSWORD:-[NOT SET]}"
        echo ""
        
        if [[ -n "$GANCIO_BASE_URL" ]]; then
          echo "Testing basic connectivity to: $GANCIO_BASE_URL"
          curl -I -s --max-time 10 "$GANCIO_BASE_URL" && echo "✅ Base URL accessible" || echo "❌ Base URL failed"
          curl -I -s --max-time 10 "$GANCIO_BASE_URL/api/events" && echo "✅ API endpoint accessible" || echo "❌ API endpoint failed"
        fi
        
    - name: Scripts Debug
      if: github.event.inputs.debug_target == 'scripts' || github.event.inputs.debug_target == 'full'  
      run: |
        echo "📜 SCRIPTS ANALYSIS:"
        echo "Python environment:"
        python3 -c "import sys; print(f'Python executable: {sys.executable}')"
        python3 -c "import sys; print(f'Python path: {sys.path}')"
        echo ""
        
        echo "Testing Python imports:"
        python3 -c "import requests; print('✅ requests')" || echo "❌ requests missing"
        python3 -c "import json; print('✅ json')" || echo "❌ json missing"
        python3 -c "import os; print('✅ os')" || echo "❌ os missing"
        echo ""
        
        echo "Script files:"
        find scripts/event-sync -name "*.py" -type f 2>/dev/null | head -5 || echo "No Python scripts found"
        echo ""
        
        echo "Script permissions:"
        ls -la scripts/event-sync/*.py 2>/dev/null | head -3 || echo "No scripts to check"
```

## 📋 Quick Debug Checklist

When a workflow fails, run through this checklist:

### **1. First Look (30 seconds)**
- [ ] Which step failed first?
- [ ] Is it an environment, network, or script error?
- [ ] Are the error messages clear?

### **2. Common Issues Check (2 minutes)**
- [ ] Are all secrets set in GitHub?
- [ ] Is GANCIO_BASE_URL correct and accessible?
- [ ] Are Python scripts executable (`chmod +x`)?
- [ ] Is the virtual environment being activated?

### **3. Deep Dive (5 minutes)**
- [ ] Run the Emergency Debug workflow
- [ ] Check system resources and network
- [ ] Verify script files exist and have content
- [ ] Test connectivity manually

### **4. Local Testing (10 minutes)**
- [ ] SSH to runner and test commands manually
- [ ] Run scripts directly with same environment
- [ ] Use `act` to test locally if available

This systematic approach will help you quickly identify and resolve most GitHub Actions failures.
