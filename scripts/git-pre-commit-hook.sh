#!/bin/bash

# Git pre-commit hook to ensure formatting and critical checks pass
# This file should be placed in .git/hooks/pre-commit and made executable

set -e

echo "🔍 Running pre-commit checks..."

# Check code formatting - CRITICAL for CI/CD
echo "📝 Checking code formatting..."
if ! npm run format:check > /dev/null 2>&1; then
    echo "❌ Code formatting issues found!"
    echo ""
    echo "🔧 Run 'npm run format' to fix formatting issues"
    echo "   or run './scripts/pre-commit-validation.sh' for full validation"
    echo ""
    exit 1
fi

echo "✅ Pre-commit checks passed!"
echo "🚀 Proceeding with commit..."
