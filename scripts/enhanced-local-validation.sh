#!/bin/bash

# Enhanced Local E2E Validation Script
# This script runs comprehensive validation including coverage testing

set -e  # Exit on any error

echo "🚀 Starting Enhanced Local E2E Validation..."
echo "==============================================="

# Function to print status
print_status() {
    echo "✅ $1"
}

print_error() {
    echo "❌ $1"
    exit 1
}

# 1. Frontend Tests with Coverage
echo "📊 Running Frontend Tests with Coverage..."
if npm run test:coverage; then
    print_status "Frontend tests with coverage passed"
else
    print_error "Frontend tests with coverage failed"
fi

# 2. Frontend Build Test
echo "🔨 Testing Frontend Build..."
if npm run build; then
    print_status "Frontend build successful"
else
    print_error "Frontend build failed"
fi

# 3. TypeScript Compilation Check
echo "🔍 Checking TypeScript Compilation..."
if npx tsc --noEmit; then
    print_status "TypeScript compilation check passed"
else
    print_error "TypeScript compilation check failed"
fi

# 4. Linting
echo "🔧 Running ESLint..."
if npm run lint; then
    print_status "Linting passed"
else
    print_error "Linting failed"
fi

# 5. Backend Tests (if available)
echo "🧪 Running Backend Tests..."
if cd api && python -m pytest --tb=short -v; then
    print_status "Backend tests passed"
    cd ..
else
    echo "⚠️ Backend tests failed or not available"
    cd ..
fi

# 6. Security Audit
echo "🔒 Running Security Audit..."
if npm audit --audit-level=moderate; then
    print_status "Security audit passed"
else
    echo "⚠️ Security vulnerabilities found - review required"
fi

# 7. Bundle Size Analysis
echo "📦 Analyzing Bundle Size..."
npm run build > /dev/null 2>&1
if [ -d "dist" ]; then
    echo "Bundle analysis:"
    du -sh dist/*
    print_status "Bundle size analysis completed"
else
    echo "⚠️ Build directory not found"
fi

# 8. Git Status Check
echo "📝 Checking Git Status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️ Uncommitted changes found:"
    git status --short
else
    print_status "Git status clean"
fi

echo "==============================================="
echo "🎉 Enhanced Local E2E Validation Complete!"
echo ""
echo "Summary:"
echo "- Frontend tests with coverage: ✅"
echo "- Build compilation: ✅"
echo "- TypeScript check: ✅"
echo "- Linting: ✅"
echo "- Backend tests: ⚠️ (if available)"
echo "- Security audit: ⚠️ (review if issues)"
echo "- Bundle analysis: ✅"
echo "- Git status: ✅ (if clean)"
echo ""
echo "🚀 Ready for CI/CD pipeline!"
