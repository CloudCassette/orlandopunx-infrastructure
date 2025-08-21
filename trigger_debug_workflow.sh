#!/bin/bash
# Manual workflow trigger by creating a dispatch event

echo "🚀 Manual GitHub Actions Debug Workflow Trigger"
echo "==============================================="

# Create a temporary dispatch file to trigger workflow_dispatch
echo "Creating workflow trigger..."

# Option 1: Create an empty commit to trigger workflows
git commit --allow-empty -m "trigger: manual debug workflow run - $(date)"

echo "✅ Empty commit created to trigger workflows"
echo "📍 This will trigger any workflow_dispatch or push-triggered workflows"
echo ""
echo "🔗 Check your GitHub Actions at:"
echo "   https://github.com/CloudCassette/orlandopunx-infrastructure/actions"
echo ""
echo "⏳ The debug workflow should appear shortly..."
echo "   You can manually trigger 'Debug Event Sync' from the GitHub Actions UI"

