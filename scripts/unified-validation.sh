#!/bin/bash
# Unified Validation Script - Single Source of Truth for Local & CI/CD
# This script ensures 100% parity between local development and CI/CD validation

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global state tracking
VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

# Function to print status
print_header() {
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}===========================================${NC}"
}

print_step() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    # Don't increment error counter for warnings
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((VALIDATION_ERRORS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if we're in the right directory
check_environment() {
    if [ ! -f "package.json" ]; then
        print_error "package.json not found. Run this script from the project root."
        exit 1
    fi

    if [ ! -f "pytest.ini" ]; then
        print_error "pytest.ini not found. This doesn't appear to be the Sutra project root."
        exit 1
    fi

    print_success "Environment validation passed"
}

# Function to check git status (only in local mode)
check_git_status() {
    if [ "$1" = "local" ]; then
        print_step "Checking git status..."

        if ! git rev-parse --git-dir > /dev/null 2>&1; then
            print_error "Not in a git repository"
            exit 1
        fi

        if ! git diff --quiet; then
            print_warning "You have unstaged changes. Consider staging them first."
        fi

        if ! git diff --cached --quiet; then
            print_info "You have staged changes that will be committed."
        fi

        print_success "Git status checked"
    fi
}

# Step 1: Code Formatting Validation (CRITICAL - must run first)
validate_formatting() {
    print_step "Step 1: Code Formatting Validation"

    if npm run format:check > /dev/null 2>&1; then
        print_success "Code formatting is consistent"
    else
        print_error "Code formatting issues found"
        echo ""
        echo "🔧 To fix formatting issues, run:"
        echo "   npm run format"
        echo ""
        echo "📋 Files with formatting issues:"
        npm run format:check 2>/dev/null | grep "\[warn\]" | sed 's/\[warn\] /   - /' || true
        return 1
    fi
}

# Step 2: TypeScript Compilation
validate_typescript() {
    print_step "Step 2: TypeScript Compilation"

    if npm run type-check > /dev/null 2>&1; then
        print_success "TypeScript compilation successful"
    else
        print_error "TypeScript compilation failed"
        echo ""
        echo "🔧 To see detailed errors, run:"
        echo "   npm run type-check"
        return 1
    fi
}

# Step 3: ESLint Validation
validate_linting() {
    print_step "Step 3: ESLint Validation"

    if npm run lint > /dev/null 2>&1; then
        print_success "ESLint validation passed"
    else
        print_error "ESLint validation failed"
        echo ""
        echo "🔧 To see detailed errors, run:"
        echo "   npm run lint"
        echo ""
        echo "🔧 To auto-fix some issues, run:"
        echo "   npm run lint:fix"
        return 1
    fi
}

# Step 4: Package Security Audit
validate_security() {
    print_step "Step 4: Security Audit"

    if npm audit --audit-level=high > /dev/null 2>&1; then
        print_success "Security audit passed"
    else
        print_warning "Security vulnerabilities found"
        echo ""
        echo "🔧 To see detailed security report, run:"
        echo "   npm audit"
        echo ""
        echo "🔧 To auto-fix some vulnerabilities, run:"
        echo "   npm audit fix"
        # Don't fail on security warnings in development
    fi
}

# Step 5: Frontend Unit Tests
validate_frontend_tests() {
    print_step "Step 5: Frontend Unit Tests"

    if npm test -- --run --passWithNoTests > /dev/null 2>&1; then
        print_success "Frontend tests passed"
    else
        print_error "Frontend tests failed"
        echo ""
        echo "🔧 To see detailed test results, run:"
        echo "   npm test"
        return 1
    fi
}

# Step 6: Backend Unit Tests (Python)
validate_backend_tests() {
    print_step "Step 6: Backend Unit Tests (Python)"

    # Check if Python virtual environment exists
    if [ -d "api/.venv" ]; then
        source api/.venv/bin/activate 2>/dev/null || true
    fi

    cd api
    if python -m pytest --tb=short -q > /dev/null 2>&1; then
        print_success "Backend tests passed"
    else
        print_error "Backend tests failed"
        echo ""
        echo "🔧 To see detailed test results, run:"
        echo "   cd api && python -m pytest"
        cd ..
        return 1
    fi
    cd ..
}

# Step 7: Build Validation
validate_build() {
    print_step "Step 7: Build Validation"

    if npm run build > /dev/null 2>&1; then
        print_success "Build validation passed"
    else
        print_error "Build validation failed"
        echo ""
        echo "🔧 To see detailed build errors, run:"
        echo "   npm run build"
        return 1
    fi
}

# Step 8: Schema Validation (Sutra-specific)
validate_schemas() {
    print_step "Step 8: Schema Validation"

    if [ -f "validate-systematic-resolution.sh" ]; then
        if ./validate-systematic-resolution.sh > /dev/null 2>&1; then
            print_success "Schema validation passed"
        else
            print_warning "Schema validation issues found"
            echo ""
            echo "🔧 To see detailed schema validation, run:"
            echo "   ./validate-systematic-resolution.sh"
        fi
    else
        print_info "Schema validation script not found, skipping"
    fi
}

# Main validation function
run_validation() {
    local mode=${1:-"local"}
    local steps=${2:-"all"}

    print_header "🚀 Unified Validation Pipeline ($mode mode)"

    # Environment check
    check_environment
    check_git_status "$mode"

    echo ""
    print_info "Running validation steps..."
    echo ""

    # Critical formatting check first (fail-fast)
    if [[ "$steps" == "all" || "$steps" == *"format"* ]]; then
        validate_formatting || exit 1
    fi

    # Core validation steps
    if [[ "$steps" == "all" || "$steps" == *"typescript"* ]]; then
        validate_typescript || exit 1
    fi

    if [[ "$steps" == "all" || "$steps" == *"lint"* ]]; then
        validate_linting || exit 1
    fi

    if [[ "$steps" == "all" || "$steps" == *"security"* ]]; then
        validate_security
    fi

    if [[ "$steps" == "all" || "$steps" == *"frontend-tests"* ]]; then
        validate_frontend_tests || exit 1
    fi

    if [[ "$steps" == "all" || "$steps" == *"backend-tests"* ]]; then
        validate_backend_tests || exit 1
    fi

    if [[ "$steps" == "all" || "$steps" == *"build"* ]]; then
        validate_build || exit 1
    fi

    if [[ "$steps" == "all" || "$steps" == *"schemas"* ]]; then
        validate_schemas
    fi

    # Final summary
    echo ""
    print_header "📊 Validation Summary"

    if [ $VALIDATION_ERRORS -eq 0 ]; then
        print_success "All critical validations passed! ✨"
        if [ $VALIDATION_WARNINGS -gt 0 ]; then
            print_warning "$VALIDATION_WARNINGS warning(s) found (non-blocking)"
        fi
        echo ""
        print_info "Ready for CI/CD pipeline! 🚀"
        return 0
    else
        print_error "$VALIDATION_ERRORS critical error(s) found"
        if [ $VALIDATION_WARNINGS -gt 0 ]; then
            print_warning "$VALIDATION_WARNINGS warning(s) found"
        fi
        echo ""
        print_info "Please fix the errors above before proceeding."
        return 1
    fi
}

# Help function
show_help() {
    echo "🔧 Unified Validation Script"
    echo ""
    echo "Usage: $0 [mode] [steps]"
    echo ""
    echo "Modes:"
    echo "  local     - Local development validation (default)"
    echo "  ci        - CI/CD validation (no git checks)"
    echo ""
    echo "Steps (comma-separated or 'all'):"
    echo "  format           - Code formatting check"
    echo "  typescript       - TypeScript compilation"
    echo "  lint             - ESLint validation"
    echo "  security         - Security audit"
    echo "  frontend-tests   - Frontend unit tests"
    echo "  backend-tests    - Backend unit tests"
    echo "  build            - Build validation"
    echo "  schemas          - Schema validation"
    echo "  all              - All steps (default)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all validations in local mode"
    echo "  $0 ci                        # Run all validations in CI mode"
    echo "  $0 local format,typescript   # Run only formatting and TypeScript checks"
    echo "  $0 local frontend-tests      # Run only frontend tests"
}

# Main execution
main() {
    case "${1:-}" in
        -h|--help|help)
            show_help
            exit 0
            ;;
        *)
            run_validation "$@"
            ;;
    esac
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
