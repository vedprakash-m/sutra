#!/bin/bash

# Comprehensive Local Validation Script for Sutra
# This script runs all validation checks locally to catch issues before CI/CD

set -e

echo "🚀 Starting Comprehensive Local Validation"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in the right directory
check_directory() {
    if [ ! -f "package.json" ] || [ ! -f "pytest.ini" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_warning "Python virtual environment not found. Creating one..."
        python3 -m venv .venv
    fi

    print_success "Dependencies check passed"
}

# Function to install/update dependencies
install_dependencies() {
    print_status "Installing/updating dependencies..."

    # Install Node.js dependencies
    npm install

    # Activate virtual environment and install Python dependencies
    source .venv/bin/activate
    # Use CI requirements to avoid grpcio compilation issues
    pip install -r api/requirements-ci.txt
    pip install pytest pytest-cov pytest-asyncio

    print_success "Dependencies installed"
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running frontend tests..."

    npm test -- --coverage --watchAll=false --passWithNoTests

    if [ $? -eq 0 ]; then
        print_success "Frontend tests passed"
        return 0
    else
        print_error "Frontend tests failed"
        return 1
    fi
}

# Function to run backend tests
run_backend_tests() {
    print_status "Running backend tests..."

    cd api
    source .venv/bin/activate

    # Run with verbose output and coverage
    python -m pytest --cov=. --cov-report=term --cov-report=html -v --tb=short

    local exit_code=$?
    cd ..

    if [ $exit_code -eq 0 ]; then
        print_success "Backend tests passed"
        return 0
    else
        print_error "Backend tests failed"
        return 1
    fi
}

# Function to run linting
run_linting() {
    print_status "Running linting checks..."

    # Frontend linting (if eslint is configured)
    if [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ]; then
        npm run lint 2>/dev/null || print_warning "Frontend linting not configured or failed"
    fi

    # Backend linting (if configured)
    cd api
    source .venv/bin/activate

    # Run flake8 if available
    if command -v flake8 &> /dev/null; then
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || print_warning "Backend linting warnings found"
    fi

    cd ..
    print_success "Linting checks completed"
}

# Function to run type checking
run_type_checking() {
    print_status "Running type checking..."

    # Frontend type checking
    npm run type-check 2>/dev/null || print_warning "Frontend type checking not configured or failed"

    # Backend type checking (if mypy is available)
    cd api
    source .venv/bin/activate

    if command -v mypy &> /dev/null; then
        mypy . --ignore-missing-imports 2>/dev/null || print_warning "Backend type checking warnings found"
    fi

    cd ..
    print_success "Type checking completed"
}

# Function to check for security vulnerabilities
run_security_checks() {
    print_status "Running security checks..."

    # Frontend security audit
    npm audit --audit-level=moderate 2>/dev/null || print_warning "Frontend security audit found issues"

    # Backend security check with modern safety scanner
    cd api
    source .venv/bin/activate

    # Install safety if not available
    if ! command -v safety &> /dev/null; then
        print_status "Installing safety scanner..."
        pip install safety
    fi

    # Test with screen output format (no interactive prompt)
    print_status "Running safety scan in screen mode..."
    if safety scan --output screen; then
        print_success "Backend security scan passed"
    else
        print_error "Backend security scan failed - this will cause CI/CD failure"
        cd ..
        return 1
    fi

    cd ..
    print_success "Security checks completed"
}

# Function to validate build
validate_build() {
    print_status "Validating build process..."

    # Build frontend
    npm run build

    if [ $? -eq 0 ]; then
        print_success "Build validation passed"
        return 0
    else
        print_error "Build validation failed"
        return 1
    fi
}

# Function to run infrastructure validation
run_infrastructure_validation() {
    print_status "Running infrastructure validation..."

    # Check if infrastructure validation script exists
    if [ -f "scripts/validate-infrastructure.sh" ]; then
        # Test script syntax first
        if ! bash -n scripts/validate-infrastructure.sh; then
            print_error "Infrastructure validation script has syntax errors"
            return 1
        fi

        # Run in dry-run mode (no Azure CLI required)
        print_status "Running infrastructure validation in dry-run mode..."
        if bash scripts/validate-infrastructure.sh --dry-run; then
            print_success "Infrastructure validation passed"
            return 0
        else
            print_error "Infrastructure validation failed - this will fail in CI/CD"
            return 1
        fi
    else
        print_warning "Infrastructure validation script not found"
        return 0
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)
    local failed_checks=0

    check_directory
    check_dependencies
    install_dependencies

    echo ""
    echo "🧪 Running Test Suite"
    echo "===================="

    # Run tests
    if ! run_frontend_tests; then
        ((failed_checks++))
    fi

    if ! run_backend_tests; then
        ((failed_checks++))
    fi

    echo ""
    echo "🔍 Running Quality Checks"
    echo "========================="

    run_linting
    run_type_checking
    run_security_checks

    echo ""
    echo "🏗️ Running Build Validation"
    echo "==========================="

    if ! validate_build; then
        ((failed_checks++))
    fi

    echo ""
    echo "🏗️ Running Infrastructure Validation"
    echo "===================================="

    if ! run_infrastructure_validation; then
        ((failed_checks++))
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    echo "📊 Validation Summary"
    echo "===================="
    echo "Duration: ${duration}s"

    if [ $failed_checks -eq 0 ]; then
        print_success "All validation checks passed! 🎉"
        print_success "Your code is ready for commit and CI/CD pipeline"
        exit 0
    else
        print_error "Some validation checks failed (${failed_checks} issues)"
        print_error "Please fix the issues before committing"
        exit 1
    fi
}

# Handle script interruption
trap 'print_error "Validation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
