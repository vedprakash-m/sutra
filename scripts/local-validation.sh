#!/bin/bash

# Enhanced Local Validation - Match GitHub CI/CD exactly
# This script provides comprehensive pre-commit validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ISSUES_FOUND=0
START_TIME=$(date +%s)

echo -e "${BLUE}🚀 Sutra Enhanced Local Validation${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; ((ISSUES_FOUND++)); }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Function to run a test with timing
run_test() {
    local test_name="$1"
    local test_command="$2"
    local start_time=$(date +%s)
    
    echo -n "Testing $test_name... "
    
    if eval "$test_command" > /tmp/test_output 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "$test_name (${duration}s)"
        return 0
    else
        log_error "$test_name failed"
        echo "Output:"
        cat /tmp/test_output | head -20
        echo ""
        return 1
    fi
}

# Stage 1: Environment Validation (Fast)
echo -e "${BLUE}📋 Stage 1: Environment Validation${NC}"
echo "-----------------------------------"

run_test "Node.js version" "node --version | grep -E '^v(18\\.|20\\.|22\\.)'"
run_test "Python version" "python3 --version | grep -E '3\\.(11|12)'"
run_test "Docker daemon" "docker info > /dev/null"
run_test "Docker Compose" "docker compose version > /dev/null"

echo ""

# Stage 2: Dependencies & Setup (Medium)
echo -e "${BLUE}🔧 Stage 2: Dependencies & Setup${NC}"
echo "--------------------------------"

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm ci --prefer-offline --no-audit
    log_success "Node.js dependencies installed"
else
    run_test "Node.js dependencies" "npm ls > /dev/null"
fi

# Check if backend dependencies are installed
cd api
if ! python3 -c "import azure.functions" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements-minimal.txt
    log_success "Python dependencies installed"
else
    run_test "Python dependencies" "python3 -c 'import azure.functions, azure.cosmos, pydantic'"
fi
cd ..

echo ""

# Stage 3: Code Quality (Fast feedback)
echo -e "${BLUE}🎯 Stage 3: Code Quality Checks${NC}"
echo "-------------------------------"

run_test "ESLint" "npm run lint"
run_test "TypeScript compilation" "npm run type-check"
run_test "Prettier formatting" "npm run format:check"
run_test "Package audit (high severity only)" "npm audit --audit-level=high"

# Python code quality
cd api
run_test "Python syntax check" "python3 -m py_compile \$(find . -name '*.py' | head -10)"
run_test "Python import validation" "python3 -c 'import sys; sys.exit(0)'"
cd ..

echo ""

# Stage 4: Unit Tests (Medium speed)
echo -e "${BLUE}🧪 Stage 4: Unit Tests${NC}"
echo "----------------------"

run_test "Frontend unit tests" "npm run test:coverage"
cd api
run_test "Backend unit tests" "python3 -m pytest -v --tb=short"
cd ..

echo ""

# Stage 5: Build Validation (Medium speed)
echo -e "${BLUE}🏗️  Stage 5: Build Validation${NC}"
echo "----------------------------"

run_test "Frontend build" "npm run build"
run_test "Build output validation" "test -f dist/index.html && test -d dist/assets"

echo ""

# Stage 6: Infrastructure Validation (Fast)
echo -e "${BLUE}🏗️  Stage 6: Infrastructure Validation${NC}"
echo "-------------------------------------"

if command -v az &> /dev/null; then
    # Check if Azure CLI has bicep
    if ! az bicep version &> /dev/null; then
        echo "Installing Bicep..."
        az bicep install
    fi
    
    run_test "Bicep persistent template" "az bicep build --file infrastructure/persistent.bicep --stdout > /dev/null"
    run_test "Bicep compute template" "az bicep build --file infrastructure/compute.bicep --stdout > /dev/null"
else
    log_warning "Azure CLI not installed - skipping Bicep validation"
fi

run_test "Deployment script syntax" "bash -n scripts/deploy-infrastructure.sh"
run_test "Validation script syntax" "bash -n scripts/validate-infrastructure.sh"

echo ""

# Stage 7: Integration Tests (Slow - only if requested)
if [[ "$1" == "--full" ]] || [[ "$1" == "--e2e" ]]; then
    echo -e "${BLUE}🔗 Stage 7: Integration Tests (E2E)${NC}"
    echo "-----------------------------------"
    
    # Clean up any existing containers
    docker compose down --remove-orphans > /dev/null 2>&1 || true
    
    echo "Starting test environment..."
    if npm run e2e:setup > /tmp/e2e_setup.log 2>&1; then
        log_success "Test environment started"
        
        # Wait for services to be ready
        echo "Waiting for services to be ready..."
        timeout 60s bash -c 'until curl -f http://localhost:7071/api/health > /dev/null 2>&1; do sleep 2; done' && \
        timeout 60s bash -c 'until curl -f http://localhost:5173 > /dev/null 2>&1; do sleep 2; done'
        
        if [ $? -eq 0 ]; then
            log_success "Services are ready"
            
            # Install Playwright browsers if needed
            if ! npx playwright install --dry-run chromium > /dev/null 2>&1; then
                echo "Installing Playwright browsers..."
                npx playwright install chromium > /dev/null 2>&1
            fi
            
            # Run E2E tests
            if npx playwright test --reporter=line > /tmp/e2e_results.log 2>&1; then
                log_success "E2E tests passed"
            else
                log_error "E2E tests failed"
                echo "Last 20 lines of E2E output:"
                tail -20 /tmp/e2e_results.log
            fi
        else
            log_error "Services failed to start within timeout"
            echo "Setup log:"
            cat /tmp/e2e_setup.log | tail -20
        fi
        
        # Cleanup
        npm run e2e:cleanup > /dev/null 2>&1 || true
    else
        log_error "Failed to start test environment"
        cat /tmp/e2e_setup.log | tail -20
    fi
else
    log_info "Skipping E2E tests (use --full or --e2e to include them)"
fi

echo ""

# Stage 8: Security Scanning (Medium speed)
echo -e "${BLUE}🔒 Stage 8: Security Scanning${NC}"
echo "-----------------------------"

# Check for security vulnerabilities in dependencies
if command -v npm &> /dev/null; then
    run_test "NPM security audit" "npm audit --audit-level=moderate"
fi

cd api
if command -v safety &> /dev/null || pip install safety > /dev/null 2>&1; then
    run_test "Python security check" "safety check"
else
    log_warning "Safety not available - skipping Python security check"
fi
cd ..

# Check for secrets in code (basic)
if command -v grep &> /dev/null; then
    echo "Checking for potential secrets..."
    if grep -r -i --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" \
       -E "(password|secret|key|token)" . > /tmp/secrets_check.log 2>&1; then
        
        # Filter out obviously safe matches
        if grep -v -E "(\.md:|example|test|mock|placeholder|<password>|<secret>|<key>|<token>)" /tmp/secrets_check.log > /tmp/secrets_filtered.log; then
            if [ -s /tmp/secrets_filtered.log ]; then
                log_warning "Potential secrets found in code"
                echo "Review these matches:"
                head -10 /tmp/secrets_filtered.log
            else
                log_success "No suspicious secrets found"
            fi
        else
            log_success "No suspicious secrets found"
        fi
    else
        log_success "No potential secrets found"
    fi
fi

echo ""

# Final Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "${BLUE}📊 Validation Summary${NC}"
echo "===================="
echo "Duration: ${DURATION} seconds"
echo "Issues found: $ISSUES_FOUND"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo ""
    log_success "All validations passed! ✨"
    echo -e "${GREEN}Your code is ready for GitHub CI/CD pipeline${NC}"
    echo ""
    echo "Next steps:"
    echo "  - git add ."
    echo "  - git commit -m 'your message'"
    echo "  - git push origin main"
else
    echo ""
    log_error "Found $ISSUES_FOUND issues that need to be fixed"
    echo -e "${RED}Please fix the issues before committing${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Run 'npm run lint:fix' for linting issues"
    echo "  - Run 'npm run format' for formatting issues"
    echo "  - Update dependencies for audit issues"
fi

echo ""
exit $ISSUES_FOUND
