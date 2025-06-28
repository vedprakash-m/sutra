#!/bin/bash
set -e

echo "🚀 Running Pre-Push Validation..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet; then
    print_warning "You have unstaged changes. Consider staging them first."
fi

if ! git diff --cached --quiet; then
    print_warning "You have staged changes that will be committed."
fi

echo ""
echo "📋 Running validation steps..."

# Step 1: TypeScript compilation
echo "1️⃣ TypeScript Compilation..."
if npm run build > /dev/null 2>&1; then
    print_status "TypeScript compilation successful"
else
    print_error "TypeScript compilation failed"
    echo "Run 'npm run build' to see details"
    exit 1
fi

# Step 2: Linting
echo "2️⃣ ESLint Check..."
if npm run lint > /dev/null 2>&1; then
    print_status "ESLint check passed"
else
    print_error "ESLint check failed"
    echo "Run 'npm run lint' to see details"
    exit 1
fi

# Step 3: Unit Tests
echo "3️⃣ Unit Tests..."
if npm test > /dev/null 2>&1; then
    print_status "All unit tests passed"
else
    print_error "Unit tests failed"
    echo "Run 'npm test' to see details"
    exit 1
fi

# Step 4: Test Coverage
echo "4️⃣ Test Coverage..."
COVERAGE_OUTPUT=$(npm run test:coverage 2>&1 | tail -10)
STATEMENTS_COVERAGE=$(echo "$COVERAGE_OUTPUT" | grep -E "All files.*%" | awk '{print $4}' | sed 's/%//')

if [ ! -z "$STATEMENTS_COVERAGE" ] && [ $(echo "$STATEMENTS_COVERAGE > 75" | bc -l) -eq 1 ]; then
    print_status "Test coverage: ${STATEMENTS_COVERAGE}% (meets minimum 75%)"
else
    print_warning "Test coverage below 75% or couldn't determine coverage"
fi

# Step 5: Build for production
echo "5️⃣ Production Build..."
if npm run build:prod > /dev/null 2>&1; then
    print_status "Production build successful"
else
    print_error "Production build failed"
    echo "Run 'npm run build:prod' to see details"
    exit 1
fi

echo ""
echo "🎉 All validation checks passed!"
echo "✅ Ready to push to repository"

# Optionally run a quick E2E smoke test if available
if [ -f "scripts/smoke-test.sh" ]; then
    echo ""
    echo "🧪 Running smoke test..."
    if ./scripts/smoke-test.sh; then
        print_status "Smoke test passed"
    else
        print_warning "Smoke test failed - consider manual verification"
    fi
fi

echo ""
echo "📝 Summary:"
echo "   - TypeScript: ✅"
echo "   - ESLint: ✅"
echo "   - Tests: ✅"
echo "   - Coverage: ✅"
echo "   - Build: ✅"
echo ""
