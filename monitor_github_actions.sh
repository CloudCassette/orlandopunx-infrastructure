#!/bin/bash
# Monitor GitHub Actions runs locally

echo "🔍 GitHub Actions Monitor"
echo "========================"

# Function to check runner status
check_runner_status() {
    echo "🤖 Runner Status:"
    if systemctl is-active --quiet actions.runner.*; then
        echo "✅ Runner service is active"
        ps aux | grep "Runner.Listener" | grep -v grep | head -1
    else
        echo "❌ Runner service not active"
    fi
    echo ""
}

# Function to check recent logs
check_recent_logs() {
    echo "📜 Recent Runner Activity (last 10 lines):"
    sudo journalctl -u actions.runner.* -n 10 --no-pager 2>/dev/null || echo "Cannot access runner logs"
    echo ""
}

# Function to monitor workflow files
check_workflow_files() {
    echo "📋 Available Workflows:"
    ls -la .github/workflows/ | grep -E "\.(yml|yaml)$"
    echo ""
}

# Function to check for running processes
check_running_processes() {
    echo "🏃 Python/Sync Processes:"
    ps aux | grep -E "(python.*sync|automated_sync)" | grep -v grep | head -5
    if [ $? -ne 0 ]; then
        echo "No sync processes currently running"
    fi
    echo ""
}

# Function to tail runner logs in real time
tail_runner_logs() {
    echo "📡 Tailing Runner Logs (Ctrl+C to stop):"
    echo "========================================="
    sudo journalctl -u actions.runner.* -f 2>/dev/null || echo "Cannot access runner logs - check permissions"
}

# Main monitoring loop
while true; do
    clear
    echo "🔍 GitHub Actions Live Monitor - $(date)"
    echo "========================================"
    
    check_runner_status
    check_workflow_files
    check_running_processes
    
    echo "📊 Commands:"
    echo "  [l] Check recent logs"
    echo "  [t] Tail logs in real-time"  
    echo "  [r] Refresh status"
    echo "  [q] Quit"
    echo ""
    
    echo "🔗 GitHub Actions URL:"
    echo "   https://github.com/CloudCassette/orlandopunx-infrastructure/actions"
    echo ""
    
    read -t 5 -n 1 choice
    case $choice in
        l|L) check_recent_logs; read -n 1 -s -r -p "Press any key to continue...";;
        t|T) tail_runner_logs;;
        r|R) continue;;
        q|Q) break;;
        *) continue;;
    esac
done

echo "👋 Monitoring stopped."
