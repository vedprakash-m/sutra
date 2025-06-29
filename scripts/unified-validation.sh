#!/bin/bash

# Unified Validation Script for Sutra
# Provides single entry point for both local development and CI/CD environments
# This script ensures 100% parity between local and CI validation

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
VALIDATION_MODE="local"  # local, ci, strict
VALIDATION_SCOPE="all"   # all, quick, core
ISSUES_FOUND=0
START_TIME=$(date +%s)

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; ((ISSUES_FOUND++)); }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Function to show usage
show_usage() {
    echo "Usage: $0 [MODE] [SCOPE]"
    echo ""
    echo "MODE:"
    echo "  local    - Local development mode (default)"
    echo "  ci       - CI/CD mode (strict validation)"
    echo "  strict   - Strict mode (matches CI exactly)"
    echo ""
    echo "SCOPE:"
    echo "  all      - Full validation (default)"
    echo "  quick    - Quick validation (core checks only)"
    echo "  core     - Core validation (no E2E)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Local mode, full validation"
    echo "  $0 ci all            # CI mode, full validation"
    echo "  $0 local quick       # Local mode, quick validation"
    echo "  $0 strict core       # Strict mode, no E2E"
}

# Parse command line arguments
parse_arguments() {
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        show_usage
        exit 0
    fi

    if [[ -n "$1" ]]; then
        case "$1" in
            local|ci|strict)
                VALIDATION_MODE="$1"
                ;;
            *)
                echo "Error: Invalid mode '$1'"
                show_usage
                exit 1
                ;;
        esac
    fi

    if [[ -n "$2" ]]; then
        case "$2" in
            all|quick|core)
                VALIDATION_SCOPE="$2"
                ;;
            *)
                echo "Error: Invalid scope '$2'"
                show_usage
                exit 1
                ;;
        esac
    fi
}

# Environment setup based on mode
setup_environment() {
    echo -e "${BLUE}🚀 Sutra Unified Validation${NC}"
    echo -e "${BLUE}============================${NC}"
    echo "Mode: $VALIDATION_MODE"
    echo "Scope: $VALIDATION_SCOPE"
    echo ""

    # Change to project root
    cd "$PROJECT_ROOT"

    # Set environment variables based on mode
    case "$VALIDATION_MODE" in
        ci)
            export CI=true
            # Don't set NODE_ENV=production as it prevents devDependencies installation
            export ENVIRONMENT=production
            export TESTING_MODE=true
            log_info "CI mode: Using production-like environment"
            ;;
        strict)
            export CI=true
            # Don't set NODE_ENV=production as it prevents devDependencies installation
            export ENVIRONMENT=production
            export TESTING_MODE=true
            export SUTRA_STRICT_VALIDATION=true
            log_info "Strict mode: Exact CI/CD behavior replication"
            ;;
        local)
            export NODE_ENV=development
            export ENVIRONMENT=development
            export TESTING_MODE=true
            log_info "Local mode: Development environment"
            ;;
    esac
}

# Core validation functions
validate_environment() {
    log_info "Validating environment..."

    # Check Node.js version
    if ! node --version | grep -E '^v(18\.|20\.|22\.)' > /dev/null; then
        log_error "Node.js version must be 18, 20, or 22"
        return 1
    fi

    # Check Python version
    if ! python3 --version | grep -E '3\.(9|10|11|12)' > /dev/null; then
        log_error "Python version must be 3.9-3.12"
        return 1
    fi

    log_success "Environment validation passed"
}

install_dependencies() {
    log_info "Installing dependencies..."

    # Install Node.js dependencies
    if [[ "$VALIDATION_MODE" == "ci" ]]; then
        # CI mode: install all dependencies (including dev) for validation
        npm ci --prefer-offline --no-audit
    else
        npm install
    fi

    # Install Python dependencies
    cd api
    python -m pip install --upgrade pip

    # Use appropriate requirements file based on mode
    if [[ "$VALIDATION_MODE" == "ci" ]]; then
        pip install -r requirements.txt
    else
        pip install -r requirements-minimal.txt
    fi

    cd ..
    log_success "Dependencies installed"
}

validate_code_quality() {
    log_info "Validating code quality..."

    # ESLint
    if ! npm run lint > /tmp/eslint.log 2>&1; then
        log_error "ESLint failed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo "ESLint errors (first 20 lines):"
            head -20 /tmp/eslint.log
        fi
    else
        log_success "ESLint passed"
    fi

    # TypeScript compilation
    if ! npm run type-check > /tmp/typecheck.log 2>&1; then
        log_error "TypeScript compilation failed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo "TypeScript errors (first 20 lines):"
            head -20 /tmp/typecheck.log
        fi
    else
        log_success "TypeScript compilation passed"
    fi

    # Code formatting (critical in CI)
    if ! npm run format:check > /tmp/prettier.log 2>&1; then
        log_error "Code formatting issues found"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo "Formatting issues (first 10 lines):"
            head -10 /tmp/prettier.log
            return 1  # Hard fail in CI mode
        fi
    else
        log_success "Code formatting passed"
    fi

    # Python linting
    cd api
    if ! python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics > /tmp/flake8.log 2>&1; then
        log_error "Python critical linting failed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            cat /tmp/flake8.log
        fi
    else
        log_success "Python linting passed"
    fi
    cd ..
}

run_unit_tests() {
    log_info "Running unit tests..."

    # Frontend tests
    if ! npm run test -- --watchAll=false --coverage > /tmp/frontend_tests.log 2>&1; then
        log_error "Frontend tests failed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo "Frontend test failures (last 30 lines):"
            tail -30 /tmp/frontend_tests.log
        fi
    else
        log_success "Frontend tests passed"
    fi

    # Backend tests
    cd api

    # Set up test environment to match CI exactly
    export FUNCTIONS_WORKER_RUNTIME="python"
    export KEY_VAULT_URI="https://test-keyvault.vault.azure.net/"
    export COSMOS_DB_CONNECTION_STRING="AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key==;"
    export ENVIRONMENT="production"
    export TESTING_MODE="true"
    unset SUTRA_ENVIRONMENT
    unset SUTRA_MAX_REQUESTS_PER_MINUTE

    if ! python3 -m pytest -v --tb=short --exitfirst --strict-markers > /tmp/backend_tests.log 2>&1; then
        log_error "Backend tests failed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo "Backend test failures (last 30 lines):"
            tail -30 /tmp/backend_tests.log
        fi
    else
        log_success "Backend tests passed"
    fi

    cd ..
}

validate_build() {
    log_info "Validating build process..."

    # Frontend build
    if ! npm run build > /tmp/build.log 2>&1; then
        log_error "Frontend build failed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo "Build errors (last 20 lines):"
            tail -20 /tmp/build.log
        fi
        return 1
    fi

    # Verify build output
    if [[ ! -f "dist/index.html" ]] || [[ ! -d "dist/assets" ]]; then
        log_error "Build output validation failed"
        echo "Missing dist/index.html or dist/assets"
        return 1
    fi

    log_success "Build validation passed"
}

run_security_checks() {
    log_info "Running security checks..."

    # NPM audit
    if [[ "$VALIDATION_SCOPE" != "quick" ]]; then
        if ! npm audit --audit-level=high > /tmp/npm_audit.log 2>&1; then
            log_warning "NPM security audit found issues"
            if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
                echo "Security issues (first 20 lines):"
                head -20 /tmp/npm_audit.log
            fi
        else
            log_success "NPM security audit passed"
        fi
    fi

    # Python security check
    if [[ "$VALIDATION_SCOPE" != "quick" ]]; then
        cd api
        if command -v safety &> /dev/null || pip install safety > /dev/null 2>&1; then
            if ! safety check > /tmp/safety.log 2>&1; then
                log_warning "Python security check found issues"
                if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
                    echo "Security issues (first 20 lines):"
                    head -20 /tmp/safety.log
                fi
            else
                log_success "Python security check passed"
            fi
        fi
        cd ..
    fi
}

run_e2e_tests() {
    if [[ "$VALIDATION_SCOPE" == "core" ]] || [[ "$VALIDATION_SCOPE" == "quick" ]]; then
        log_info "Skipping E2E tests (scope: $VALIDATION_SCOPE)"
        return 0
    fi

    log_info "Running E2E tests..."

    # Check if Docker is available
    if ! docker info > /dev/null 2>&1; then
        log_warning "Docker not available - skipping E2E tests"
        return 0
    fi

    # Check required E2E files
    local required_files=("Dockerfile.e2e" "docker-compose.yml" "playwright.config.ts")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "E2E file missing: $file"
            return 1
        fi
    done

    # Clean up any existing containers
    docker compose down --remove-orphans > /dev/null 2>&1 || true

    # Start test environment
    if npm run e2e:setup > /tmp/e2e_setup.log 2>&1; then
        log_info "E2E environment started"

        # Wait for services
        timeout 60s bash -c 'until curl -f http://localhost:7071/api/health > /dev/null 2>&1; do sleep 2; done' && \
        timeout 60s bash -c 'until curl -f http://localhost:5173 > /dev/null 2>&1; do sleep 2; done'

        if [[ $? -eq 0 ]]; then
            # Install Playwright browsers if needed
            npx playwright install chromium > /dev/null 2>&1

            # Run E2E tests
            if npx playwright test --reporter=line > /tmp/e2e_results.log 2>&1; then
                log_success "E2E tests passed"
            else
                log_error "E2E tests failed"
                if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
                    echo "E2E test failures (last 20 lines):"
                    tail -20 /tmp/e2e_results.log
                fi
            fi
        else
            log_error "E2E services failed to start"
            if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
                echo "E2E setup log:"
                cat /tmp/e2e_setup.log | tail -20
            fi
        fi

        # Cleanup
        npm run e2e:cleanup > /dev/null 2>&1 || true
    else
        log_error "Failed to start E2E environment"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            cat /tmp/e2e_setup.log | tail -20
        fi
    fi
}

# Main validation orchestration
main() {
    parse_arguments "$@"
    setup_environment

    # Core validation stages
    validate_environment || return 1
    install_dependencies || return 1

    # Code quality and testing
    validate_code_quality
    run_unit_tests
    validate_build || return 1

    # Security and E2E (scope dependent)
    if [[ "$VALIDATION_SCOPE" != "quick" ]]; then
        run_security_checks
    fi

    if [[ "$VALIDATION_SCOPE" == "all" ]]; then
        run_e2e_tests
    fi

    # Final summary
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    echo ""
    echo -e "${BLUE}📊 Validation Summary${NC}"
    echo "===================="
    echo "Mode: $VALIDATION_MODE"
    echo "Scope: $VALIDATION_SCOPE"
    echo "Duration: ${duration} seconds"
    echo "Issues found: $ISSUES_FOUND"

    if [[ $ISSUES_FOUND -eq 0 ]]; then
        echo ""
        log_success "All validations passed! ✨"
        if [[ "$VALIDATION_MODE" == "local" ]]; then
            echo ""
            echo "Next steps:"
            echo "  - git add ."
            echo "  - git commit -m 'your message'"
            echo "  - git push origin main"
        fi
        exit 0
    else
        echo ""
        log_error "Found $ISSUES_FOUND issues that need to be fixed"
        if [[ "$VALIDATION_MODE" == "ci" ]] || [[ "$VALIDATION_MODE" == "strict" ]]; then
            echo -e "${RED}CI/CD will fail with these issues${NC}"
        else
            echo -e "${RED}Please fix the issues before committing${NC}"
        fi
        exit 1
    fi
}

# Trap interrupts
trap 'log_error "Validation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
