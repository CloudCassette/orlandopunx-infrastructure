#!/bin/bash
# 🧹 Monthly Gancio Maintenance Script
# Run this monthly to check for duplicates and system health

echo "🧹 GANCIO MONTHLY MAINTENANCE"
echo "=============================="
echo "📅 Date: $(date)"
echo ""

echo "📊 Current Event Counts:"
echo "========================"
sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT 'Total events: ' || COUNT(*) FROM events;"
sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT 'Visible: ' || COUNT(*) FROM events WHERE is_visible = 1;"
sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT 'Hidden: ' || COUNT(*) FROM events WHERE is_visible = 0;"

echo ""
echo "🔍 Duplicate Check:"
echo "==================="
DUPLICATES=$(sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT COUNT(*) FROM (SELECT title, COUNT(*) as count FROM events GROUP BY title HAVING count > 1);")

if [ "$DUPLICATES" -eq 0 ]; then
    echo "✅ No duplicates found!"
else
    echo "⚠️  Found $DUPLICATES duplicate title groups:"
    sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT title || ' (' || COUNT(*) || ' copies)' FROM events GROUP BY title HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC LIMIT 10;"
    echo ""
    echo "💡 Run cleanup tool: sudo -u gancio python3 gancio_bulk_cleanup.py"
fi

echo ""
echo "🔧 System Status:"
echo "=================="
if systemctl is-active --quiet gancio; then
    echo "✅ Gancio service running"
else
    echo "❌ Gancio service not running"
fi

if curl -f -s -m 5 "http://localhost:13120/api/events" > /dev/null; then
    echo "✅ API responding"
else
    echo "❌ API not responding"
fi

echo ""
echo "📋 GitHub Actions Status:"
echo "========================="
echo "💡 Check recent workflow runs at: https://github.com/CloudCassette/orlandopunx-infrastructure/actions"

echo ""
echo "🎯 Maintenance complete!"
