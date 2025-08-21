#!/bin/bash
echo "🤖 GitHub Actions Runner Health Check"
echo "====================================="
echo "⏰ $(date)"

RUNNER_SERVICE="actions.runner.CloudCassette-orlandopunx-infrastructure.orlandopunx-server.service"

# Check GitHub Actions Runner
echo ""
echo "🔍 GitHub Actions Runner Status:"
if systemctl is-active --quiet "$RUNNER_SERVICE"; then
    echo "✅ GitHub Actions Runner is running"
    echo "📋 Recent jobs:"
    journalctl -u "$RUNNER_SERVICE" --no-pager -n 3 | grep -E "(Running job|completed with result)" | tail -3 || echo "No recent job logs"
else
    echo "❌ GitHub Actions Runner is NOT running"
fi

# Check Gancio
echo ""
echo "🎵 Gancio Service:"
if systemctl is-active --quiet gancio; then
    echo "✅ Gancio service is running"
    if curl -f -s -m 5 "http://localhost:13120/api/events" > /dev/null; then
        event_count=$(curl -s -m 5 "http://localhost:13120/api/events" | jq length 2>/dev/null || echo "unknown")
        echo "✅ Gancio API accessible with $event_count events"
    else
        echo "❌ Gancio API is not accessible"
    fi
else
    echo "❌ Gancio service is NOT running"
fi

echo ""
echo "⏰ Health check completed: $(date)"
