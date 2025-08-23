#!/bin/bash

echo "🔧 Fixing pre-commit setup for orlandopunx-infrastructure"
echo "========================================================"

# Option 1: Install pre-commit system-wide (recommended)
echo "Installing pre-commit system-wide..."
pip3 install pre-commit
if [ $? -eq 0 ]; then
    echo "✅ pre-commit installed system-wide"
    
    # Reinstall the git hooks with the new pre-commit
    echo "Reinstalling pre-commit hooks..."
    pre-commit install
    echo "✅ Pre-commit hooks reinstalled"
    
    echo "🎉 Fix completed! Pre-commit should now work."
else
    echo "❌ Failed to install pre-commit system-wide"
    echo ""
    echo "Alternative: Disable pre-commit hooks"
    echo "If you don't need pre-commit hooks, you can disable them:"
    echo "  rm .git/hooks/pre-commit"
    echo "  rm .pre-commit-config.yaml"
fi

