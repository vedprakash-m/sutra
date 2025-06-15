#!/bin/bash

# Sutra Local Validation Pipeline
echo "🔍 Running Sutra local validation pipeline..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track validation results
VALIDATION_PASSED=true

# Function to log results
log_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2 passed${NC}"
    else
        echo -e "${RED}❌ $2 failed${NC}"
        VALIDATION_PASSED=false
    fi
}

echo "📋 Step 1: Running type checks..."
npm run type-check
log_result $? "TypeScript compilation"

echo ""
echo "📋 Step 2: Running linting..."
npm run lint
log_result $? "ESLint checks"

echo ""
echo "📋 Step 3: Running unit tests..."
npm test -- --watchAll=false --coverage
log_result $? "Jest unit tests"

echo ""
echo "📋 Step 4: Building frontend..."
npm run build
log_result $? "Frontend build"

echo ""
echo "📋 Step 5: Checking API structure..."
if [ -f "api/shared/__init__.py" ] && [ -f "api/requirements.txt" ]; then
    echo -e "${GREEN}✅ API structure is valid${NC}"
else
    echo -e "${RED}❌ API structure is invalid${NC}"
    VALIDATION_PASSED=false
fi

echo ""
echo "📋 Step 6: Validating Docker setup..."
docker-compose config > /dev/null 2>&1
log_result $? "Docker Compose configuration"

echo ""
echo "📋 Step 7: Running security audit..."
npm audit --audit-level moderate
log_result $? "Security audit"

echo ""
echo "📋 Step 8: Running end-to-end tests..."
# Note: This requires local services to be running
if docker-compose ps | grep -q "Up"; then
    npm run test:e2e
    log_result $? "End-to-end tests"
else
    echo -e "${YELLOW}⚠️  Skipping E2E tests - Docker services not running${NC}"
    echo "   Run 'npm run dev:local' to start services first"
fi

echo ""
echo "🎯 Validation Summary:"
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}🎉 All validations passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}💥 Some validations failed. Please fix issues before deployment.${NC}"
    exit 1
fi
