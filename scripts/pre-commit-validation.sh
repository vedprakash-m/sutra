#!/bin/bash

# Pre-commit validation script - Exact CI/CD simulation
# Usage: ./scripts/pre-commit-validation.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚦 Pre-commit Validation (CI/CD Simulation)"
echo "============================================"

# Quick validation (under 30 seconds)
echo "⚡ Running quick checks..."

# 1. Code quality (fast) - CRITICAL for CI/CD
echo "🎯 Checking code quality..."

# ESLint
npm run lint || { echo "❌ ESLint failed"; exit 1; }

# TypeScript  
npm run type-check || { echo "❌ TypeScript errors found"; exit 1; }

# Prettier formatting - MOST CRITICAL
echo "🎨 Checking code formatting (CRITICAL)..."
if ! npm run format:check; then
    echo ""
    echo "❌ CODE FORMATTING ISSUES FOUND!"
    echo "🔧 Run: npm run format"
    echo "   This will auto-fix all formatting issues"
    echo ""
    exit 1
fi

# 2. Build validation (medium)
echo "🏗️ Validating build..."
npm run build
test -f dist/index.html || { echo "❌ Build output missing"; exit 1; }

# 3. Unit tests (fast)
echo "🧪 Running unit tests..."
npm run test:ci

# 4. Backend validation (fast)
echo "🐍 Validating backend..."
cd api
python3 -m py_compile $(find . -name "*.py" | head -5) || { echo "❌ Python syntax errors"; exit 1; }
python3 -c "import azure.functions" || { echo "❌ Backend dependencies missing"; exit 1; }
cd ..

# 5. Infrastructure validation (fast)
echo "🏗️ Validating infrastructure..."
bash -n scripts/deploy-infrastructure.sh || { echo "❌ Deployment script syntax error"; exit 1; }

if command -v az >/dev/null && az bicep version >/dev/null 2>&1; then
    az bicep build --file infrastructure/compute.bicep --stdout >/dev/null || { echo "❌ Bicep validation failed"; exit 1; }
fi

# 6. Security check (fast)
echo "🔒 Basic security check..."
npm audit --audit-level=high || { echo "❌ High severity vulnerabilities found"; exit 1; }

echo "✅ All pre-commit checks passed!"
echo "💡 Your code is ready for GitHub CI/CD"
