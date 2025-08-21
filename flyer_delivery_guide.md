# 🖼️ Complete Flyer Delivery System - User Guide

## 🎯 System Overview

Your Orlando Events sync now includes complete flyer delivery to http://192.168.86.4:8081

### ✅ What Works Now

1. **GitHub Actions Sync**: Downloads event flyers to runner workspace
2. **Automatic Delivery**: Syncs flyers to web server directory 
3. **Web Server**: Serves flyers via Python gallery at http://192.168.86.4:8081
4. **Monitoring**: Real-time monitoring and sync tools

## 🛠️ Terminal Commands for Monitoring & Management

### **List and Inspect Flyer Storage**
```bash
# List all flyers in web server directory
ls -la scripts/event-sync/flyers/ | head -10

# Check flyer counts and sizes
find scripts/event-sync/flyers -name "*.jpg" -o -name "*.png" -o -name "*.gif" | wc -l
du -sh scripts/event-sync/flyers/

# Find recent flyers (last 24 hours)
find scripts/event-sync/flyers -name "*.jpg" -mtime -1 -exec ls -la {} \;
```

### **Test Flyer URL Accessibility**
```bash
# Test main gallery page
curl -s -o /dev/null -w "HTTP %{http_code}, Size: %{size_download} bytes\n" http://192.168.86.4:8081/

# Test API endpoint
curl -s http://192.168.86.4:8081/api/flyers | jq length

# Download a specific flyer
curl -O http://192.168.86.4:8081/flyers/Alphabet_Aces_5aec5297.jpg

# Test multiple flyer URLs
for flyer in $(curl -s http://192.168.86.4:8081/api/flyers | jq -r '.[0:3].[].filename'); do
  echo "Testing: $flyer"
  curl -s -o /dev/null -w "  Status: %{http_code}, Size: %{size_download} bytes\n" "http://192.168.86.4:8081/flyers/$flyer"
done
```

### **Check Web Server Logs & Status**
```bash
# Check if flyer server is running
pgrep -f "serve_flyers.py"

# See server process details
ps aux | grep serve_flyers.py | grep -v grep

# Check server accessibility
curl -s --connect-timeout 5 http://192.168.86.4:8081/ > /dev/null && echo "✅ Server accessible" || echo "❌ Server not accessible"

# Get server statistics
curl -s http://192.168.86.4:8081/api/flyers | jq 'length, .[0:3] | {filename: .filename, size: .size, modified: .modified}'
```

### **Monitor Flyer Delivery**
```bash
# Run comprehensive flyer delivery monitor
cd scripts/event-sync && ./monitor_flyer_delivery.sh

# Quick sync check
echo "Runner workspace: $(find /home/cloudcassette/actions-runner/_work/orlandopunx-infrastructure/orlandopunx-infrastructure/scripts/event-sync/flyers -name "*.jpg" 2>/dev/null | wc -l) flyers"
echo "Web server: $(find scripts/event-sync/flyers -name "*.jpg" 2>/dev/null | wc -l) flyers"

# Manual sync if needed
rsync -av --update /home/cloudcassette/actions-runner/_work/orlandopunx-infrastructure/orlandopunx-infrastructure/scripts/event-sync/flyers/ scripts/event-sync/flyers/
```

### **GitHub Actions Monitoring**
```bash
# Check recent GitHub Actions runs
sudo journalctl -u actions.runner.* -n 10 --no-pager | grep -E "(Running job|completed)"

# Monitor GitHub Actions in real-time
./monitor_github_actions.sh

# Trigger enhanced workflow manually
gh workflow run "sync-with-flyer-delivery.yml"  # (requires gh auth login)
```

## 🚀 Available Workflows

### **1. Enhanced Sync Workflow** (.github/workflows/sync-with-flyer-delivery.yml)
- **Automatic**: Runs 3x daily (9am, 3pm, 9pm EST)
- **Features**: Downloads events + delivers flyers to web server
- **Manual**: Can be triggered from GitHub Actions web interface

### **2. Original Sync Workflow** (.github/workflows/sync-willspub-events.yml) 
- **Backup**: Original working sync without flyer delivery
- **Use**: For testing or fallback

## 📊 Monitoring & Notifications

### **Real-time Monitoring**
```bash
# Interactive flyer delivery monitor
scripts/event-sync/monitor_flyer_delivery.sh

# Continuous GitHub Actions monitoring  
./monitor_github_actions.sh
```

### **Status Checks**
```bash
# Quick status check
echo "🌐 Web Server: $(pgrep -f serve_flyers.py > /dev/null && echo "✅ Running" || echo "❌ Down")"
echo "🖼️ Flyers: $(find scripts/event-sync/flyers -name "*.jpg" | wc -l) available"
echo "📡 API: $(curl -s http://192.168.86.4:8081/api/flyers > /dev/null && echo "✅ Accessible" || echo "❌ Down")"
```

## 🎯 Access Points

- **Gallery**: http://192.168.86.4:8081
- **API**: http://192.168.86.4:8081/api/flyers  
- **Direct flyer**: http://192.168.86.4:8081/flyers/[filename].jpg
- **GitHub Actions**: https://github.com/CloudCassette/orlandopunx-infrastructure/actions

## 🔧 Troubleshooting

### **If flyers aren't syncing:**
```bash
scripts/event-sync/monitor_flyer_delivery.sh
# Follow prompts to sync missing flyers
```

### **If web server is down:**
```bash
cd scripts/event-sync && python3 serve_flyers.py &
```

### **If GitHub Actions fails:**
```bash
./debug_runner_locally.sh  # Compare local vs runner environment
```

## ✅ Success Indicators

- GitHub Actions completes without errors
- Monitor shows synchronized flyer counts
- Web server responds with HTTP 200
- New flyers appear in gallery within minutes of sync
