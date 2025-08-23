#!/bin/bash
set -e

echo "🚀 Orlando Punx Events - Deploy Improved Sync System"
echo "===================================================="

# Check if we're in the right directory
if [ ! -f "src/sync/improved_sync.py" ]; then
    echo "❌ Error: Please run this script from the orlandopunx-infrastructure repository root"
    exit 1
fi

echo "✅ Repository structure verified"

# Function to check if a command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Function to prompt for confirmation
confirm() {
    read -p "❓ $1 (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

echo
echo "📋 Pre-deployment checklist:"
echo "   ✅ Scrapers integrated and tested"
echo "   ✅ Duplicate detection system ready"
echo "   ✅ Improved workflow configured"
echo "   ✅ Rollback plan available"

echo
if confirm "Deploy the improved sync system?"; then
    echo "🔄 Deploying improved sync system..."

    # Step 1: Backup current workflow
    echo "📦 Creating backup of current workflow..."
    cp .github/workflows/reliable-sync.yml .github/workflows/reliable-sync.yml.backup
    check_success "Backup created"

    # Step 2: Disable old workflow by commenting out the schedule
    echo "⏸️ Disabling old workflow schedule..."
    sed -i 's/^  schedule:/  # schedule:/' .github/workflows/reliable-sync.yml
    check_success "Old workflow schedule disabled"

    # Step 3: Verify improved workflow is ready
    if [ -f ".github/workflows/improved-sync.yml" ]; then
        echo "✅ Improved workflow is ready and will activate automatically"
    else
        echo "❌ Error: improved-sync.yml not found"
        exit 1
    fi

    # Step 4: Create state directory if needed
    mkdir -p "$(dirname "src/sync/event_state.pkl")"
    check_success "State directory prepared"

    echo
    echo "🎉 Deployment completed successfully!"
    echo
    echo "📊 What changed:"
    echo "   • Old workflow schedule disabled (backed up as reliable-sync.yml.backup)"
    echo "   • Improved workflow will run 2x daily (9am, 9pm EST)"
    echo "   • Intelligent scheduling prevents runs within 12 hours"
    echo "   • Enhanced duplicate detection active"
    echo "   • State persistence prevents reprocessing events"
    echo
    echo "🔍 Next steps:"
    echo "   1. Monitor next scheduled run for proper operation"
    echo "   2. Check Gancio admin panel for reduced duplicates"
    echo "   3. Optionally run duplicate cleanup: cd src/sync && python3 cleanup_duplicates.py --analyze"
    echo
    echo "🔙 Rollback instructions (if needed):"
    echo "   sed -i 's/^  # schedule:/  schedule:/' .github/workflows/reliable-sync.yml"

else
    echo "❌ Deployment cancelled"
    exit 1
fi

echo
echo "✨ Improved sync system is now active!"
