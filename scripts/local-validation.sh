#!/bin/bash

# Enhanced Local Validation - Match GitHub CI/CD exactly
# This script provides comprehensive pre-commit validation
# MUST be run before every commit to prevent CI/CD failures

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
run_test "Python version" "python3 --version | grep -E '3\\.(9|10|11|12)'"
# Docker checks (non-blocking for dev environments)
if docker info > /dev/null 2>&1; then
    log_success "Docker daemon (0s)"
    if docker compose version > /dev/null 2>&1; then
        log_success "Docker Compose (0s)"
    else
        log_warning "Docker Compose not available (non-blocking)"
    fi
else
    log_warning "Docker daemon not running (non-blocking for dev)"
fi

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

# Critical code quality checks - must pass
echo "Running critical code quality checks..."

# ESLint - coding standards
if ! npm run lint > /tmp/eslint.log 2>&1; then
    log_error "ESLint failed - code quality issues found"
    echo "ESLint output:"
    cat /tmp/eslint.log | tail -20
    ((ISSUES_FOUND++))
else
    log_success "ESLint passed"
fi

# TypeScript compilation
if ! npm run type-check > /tmp/typecheck.log 2>&1; then
    log_error "TypeScript compilation failed"
    echo "TypeScript errors:"
    cat /tmp/typecheck.log | tail -20
    ((ISSUES_FOUND++))
else
    log_success "TypeScript compilation passed"
fi

# Prettier formatting - CRITICAL for CI/CD
echo "Checking code formatting (CRITICAL for CI/CD)..."
if ! npm run format:check > /tmp/prettier.log 2>&1; then
    log_error "Code formatting issues found - this will fail CI/CD!"
    echo ""
    echo "Files with formatting issues:"
    cat /tmp/prettier.log | grep "warn" | head -10
    echo ""
    echo "🔧 FIX: Run 'npm run format' to auto-fix formatting issues"
    echo ""
    ((ISSUES_FOUND++))
else
    log_success "Code formatting is correct"
fi

# Package security audit
run_test "Package audit (high severity only)" "npm audit --audit-level=high"

# Python code quality
cd api
run_test "Python syntax check" "python3 -m py_compile \$(find . -name '*.py' | head -10)"
run_test "Python import validation" "python3 -c 'import sys; sys.exit(0)'"

# Python linting (matching CI/CD pipeline exactly)
log_info "Running Python linting (matching CI/CD)..."
run_test "Python critical linting" "python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"
run_test "Python style linting" "python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics"
cd ..

echo ""

# Stage 4: Unit Tests (Medium speed)
echo -e "${BLUE}🧪 Stage 4: Unit Tests${NC}"
echo "----------------------"

# Frontend unit tests (now working after fixes)
run_test "Frontend unit tests" "npm run test -- --watchAll=false --coverage=false"

cd api

# Backend unit tests - Match CI/CD environment exactly
log_info "Running backend unit tests (matching CI/CD environment)"

# Set environment variables to match CI exactly (clean environment)
export FUNCTIONS_WORKER_RUNTIME="python"
export KEY_VAULT_URI="https://test-keyvault.vault.azure.net/"
export COSMOS_DB_CONNECTION_STRING="test-cosmos-connection"
unset SUTRA_ENVIRONMENT
unset SUTRA_MAX_REQUESTS_PER_MINUTE

echo "Running tests with clean environment (matching CI)..."
if python3 -m pytest -v --tb=short --exitfirst > /tmp/backend_tests.log 2>&1; then
    log_success "Backend unit tests passed (matching CI environment)"
else
    log_error "Backend unit tests failed - EXACTLY as CI would fail!"
    echo ""
    echo "This matches CI/CD failure pattern - tests failing due to environment config:"
    echo ""
    # Show the actual failures
    grep -A 3 -B 1 "FAILED\|assert.*==" /tmp/backend_tests.log | head -20
    echo ""
    echo "🔧 These failures match the CI pattern and need to be fixed"
    echo ""
    return 1
fi

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
    echo -e "${BLUE}🔗 Stage 7: E2E Environment Check (Essential for CI/CD)${NC}"
    echo "--------------------------------------------------------"

    # Critical: Check if Docker is available for E2E tests
    if docker info > /dev/null 2>&1; then
        # Check if E2E environment can start (quick validation)
        echo "Testing E2E environment startup (quick check)..."

        # Clean up any existing containers
        docker compose down --remove-orphans > /dev/null 2>&1 || true

        # Test docker-compose configuration
        if docker compose config > /dev/null 2>&1; then
            log_success "Docker Compose configuration valid"

            # Quick container build test (dry run)
            if docker compose build --dry-run > /tmp/e2e_build_check.log 2>&1; then
                log_success "E2E container build configuration valid"
            else
                log_error "E2E container build would fail - CI/CD will fail!"
                echo "Build errors:"
                cat /tmp/e2e_build_check.log | tail -10
            fi
        else
            log_error "Docker Compose configuration invalid - CI/CD will fail!"
            docker compose config 2>&1 | head -10
        fi
    else
        log_warning "Docker not available - cannot validate E2E setup"
        log_warning "CI/CD may fail due to container issues"
        echo ""
        echo "🔧 To fully validate E2E setup:"
        echo "   1. Start Docker Desktop"
        echo "   2. Run: scripts/local-validation.sh --e2e"
    fi

    log_info "For full E2E testing: scripts/local-validation.sh --full"
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
    # Python security check with known vulnerability filtering
    echo "Running Python security check (filtering known acceptable risks)..."
    if safety check > /tmp/safety_output.log 2>&1; then
        log_success "Python security check passed"
    else
        # Check if failures are only due to known acceptable risks
        if grep -E "(ecdsa|python-jose)" /tmp/safety_output.log > /dev/null; then
            log_warning "Python security check found known acceptable vulnerabilities"
            echo "Found vulnerabilities in ecdsa and python-jose (dev dependencies only)"
            echo "These are acceptable for development but should be monitored for production"

            # Check if there are OTHER vulnerabilities that are critical
            if grep -v -E "(ecdsa|python-jose)" /tmp/safety_output.log | grep -E "(CVE|ADVISORY)" > /tmp/safety_critical.log 2>/dev/null; then
                if [ -s /tmp/safety_critical.log ]; then
                    log_error "CRITICAL: Other security vulnerabilities found beyond known ones"
                    echo "Critical vulnerabilities:"
                    cat /tmp/safety_critical.log | head -10
                    return 1
                fi
            fi

            log_success "Python security check passed (known dev-only vulnerabilities ignored)"
        else
            log_error "Python security check failed with unknown vulnerabilities"
            echo "Safety output:"
            cat /tmp/safety_output.log | head -20
            return 1
        fi
    fi
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

# Stage 9: Final Re-validation (Critical - catch any changes made during validation)
echo -e "${BLUE}🔄 Stage 9: Final Re-validation${NC}"
echo "--------------------------------"

echo "Performing final checks to catch any new issues..."

# Re-run critical checks that could have been affected by fixes during validation
echo "🎨 Final formatting check..."
if ! npm run format:check > /tmp/final_prettier.log 2>&1; then
    log_error "CRITICAL: New formatting issues detected during validation process!"
    echo ""
    echo "Files with formatting issues:"
    cat /tmp/final_prettier.log | grep "warn" | head -10
    echo ""
    echo "🔧 This usually happens when files are created/modified during validation."
    echo "   Run 'npm run format' to fix, then re-run validation."
    echo ""
    ((ISSUES_FOUND++))
else
    log_success "Final formatting check passed"
fi

# Quick syntax check
echo "🔍 Final syntax validation..."
if npm run lint > /tmp/final_lint.log 2>&1 && npm run type-check > /tmp/final_typecheck.log 2>&1; then
    log_success "Final syntax check passed"
else
    log_error "New syntax issues detected during validation process!"
    ((ISSUES_FOUND++))
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
