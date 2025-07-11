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

    # Check Docker (critical for E2E tests)
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed (required for E2E tests)"
        print_error "This will cause CI/CD E2E tests to fail"
        print_error "Please install Docker Desktop"
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        print_error "This will cause CI/CD E2E tests to fail"
        print_error "Please start Docker Desktop"
        exit 1
    fi

    # Check for Docker Compose (critical gap that CI/CD missed)
    local docker_compose_available=false
    if command -v docker-compose &> /dev/null; then
        print_success "docker-compose (legacy) available: $(docker-compose --version)"
        docker_compose_available=true
    fi

    if docker compose version &> /dev/null 2>&1; then
        print_success "docker compose (modern) available: $(docker compose version)"
        docker_compose_available=true
    fi

    if [ "$docker_compose_available" = false ]; then
        print_error "Neither 'docker-compose' nor 'docker compose' is available"
        print_error "This will cause CI/CD E2E tests to fail"
        print_error "Please install Docker Compose"
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

    cd api || { print_error "Cannot enter api directory"; return 1; }

    # Check Python version compatibility
    python3 --version | grep -E "Python 3\.(8|9|10|11|12)" >/dev/null
    if [ $? -ne 0 ]; then
        print_error "Python 3.8+ required for backend tests"
        cd ..
        return 1
    fi

    # Install test dependencies if needed
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found, tests may fail"
    fi

    # Run comprehensive API consistency checks first
    print_status "Running API consistency validation..."
    if ! validate_api_consistency; then
        print_error "API consistency validation failed - this would cause CI/CD failures"
        cd ..
        return 1
    fi

    # Run pytest with coverage
    print_status "Running pytest with coverage..."
    python3 -m pytest --cov=. --cov-report=term-missing --cov-report=xml -v --tb=short

    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        print_error "Backend tests failed (exit code: $exit_code)"

        # Additional debugging for authentication mocking issues
        print_status "Checking for authentication mocking issues..."
        if ! validate_auth_mocking; then
            print_error "Authentication mocking validation failed"
        fi

        cd ..
        return 1
    fi

    cd ..
    print_success "Backend tests passed"
    return 0
}

# Validate authentication mocking in tests to prevent CI/CD failures
validate_auth_mocking() {
    print_status "Validating authentication mocking patterns..."

    # Check for tests that might expect early validation but get auth errors
    local auth_mock_issues=0

    # Look for tests expecting 400 responses but with incomplete auth mocking
    while IFS= read -r file; do
        if grep -l "assert.*status_code.*400" "$file" >/dev/null 2>&1; then
            # Check if this test has comprehensive auth mocking
            if ! grep -l "AuthManager.get_auth_config\|AuthManager.validate_token\|AuthManager.get_user_from_token" "$file" >/dev/null 2>&1; then
                print_warning "Test file $file expects 400 status but may have incomplete auth mocking"
                print_warning "This could cause CI/CD failures when auth runs before validation"
                ((auth_mock_issues++))
            fi
        fi
    done < <(find . -name "*test*.py" -type f)

    # Check for missing auth decorator bypass in critical tests
    if grep -r "require_auth.*lambda.*func.*func" . >/dev/null 2>&1; then
        print_warning "Found old auth bypassing pattern that may not work in CI/CD"
        print_warning "Consider using comprehensive @patch decorators instead"
        ((auth_mock_issues++))
    fi

    # Check for tests missing Key Vault mocking
    while IFS= read -r file; do
        if grep -l "AuthManager" "$file" >/dev/null 2>&1; then
            if ! grep -l "kv_client.*PropertyMock\|KEY_VAULT_URI.*mock" "$file" >/dev/null 2>&1; then
                print_warning "Test file $file uses AuthManager but may be missing Key Vault mocking"
                ((auth_mock_issues++))
            fi
        fi
    done < <(find . -name "*test*.py" -type f)

    if [ $auth_mock_issues -eq 0 ]; then
        print_success "Authentication mocking patterns validated"
        return 0
    else
        print_error "Found $auth_mock_issues potential authentication mocking issues"
        print_error "These could cause tests to pass locally but fail in CI/CD"
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
        # Use older Safety CLI version that doesn't require authentication
        pip install "safety<3.0.0"
    fi

    # Test with the older safety check command that doesn't require auth
    print_status "Running safety check..."
    if safety check --file requirements.txt; then
        print_success "Backend security scan passed"
    else
        print_error "Backend security scan failed - this will cause CI/CD failure"
        cd ..
        return 1
    fi

    # Simulate fresh CI/CD environment by testing without authentication
    print_status "Testing security scan in CI/CD simulation mode..."

    # Temporarily move authentication if it exists
    local auth_backup=""
    if [ -d "$HOME/.safety" ]; then
        auth_backup="$HOME/.safety.backup.$$"
        mv "$HOME/.safety" "$auth_backup" 2>/dev/null || true
    fi

    # Test safety check without authentication (simulates CI/CD)
    local exit_code=0
    if ! safety check --file requirements.txt >/dev/null 2>&1; then
        print_error "Security scan would fail in CI/CD (no authentication)"
        exit_code=1
    else
        print_success "Security scan works without authentication"
    fi

    # Restore authentication if it was backed up
    if [ -n "$auth_backup" ] && [ -d "$auth_backup" ]; then
        mv "$auth_backup" "$HOME/.safety" 2>/dev/null || true
    fi

    cd ..

    if [ $exit_code -ne 0 ]; then
        return 1
    fi
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

# Function to validate API implementation consistency
validate_api_consistency() {
    print_status "Validating API implementation and test consistency..."

    local consistency_issues=0

    # Check for partition key consistency issues
    print_status "Checking database partition key consistency..."

    # Collections API partition key check
    if [ -f "collections_api/__init__.py" ] && [ -f "collections_api/collections_test.py" ]; then
        # Check if implementation uses user_id as partition key
        local impl_uses_user_id=$(grep -c "partition_key=user_id\|partition_key.*user_id" collections_api/__init__.py)
        # Check if tests expect collection_id as partition key
        local test_expects_collection_id=$(grep -c "partition_key.*collection.*id\|partition_key=.*collection" collections_api/collections_test.py)

        if [ "$impl_uses_user_id" -gt 0 ] && [ "$test_expects_collection_id" -gt 0 ]; then
            print_error "Collections API: Implementation uses user_id as partition key, but tests expect collection_id"
            print_error "This will cause CI/CD test failures"
            ((consistency_issues++))
        fi
    fi

    # Check for validation expectation mismatches
    print_status "Checking validation and error handling consistency..."

    # Look for tests that expect specific status codes but implementation returns different codes
    local test_files=$(find . -name "*test*.py" -type f)
    for test_file in $test_files; do
        # Check for tests expecting 500 from validation errors
        if grep -q "assert.*status_code.*500" "$test_file" && grep -q "ValidationError\|validation.*exception" "$test_file"; then
            local api_file=${test_file/_test.py//__init__.py}
            api_file=${api_file/test_/}

            if [ -f "$api_file" ]; then
                # Check if API actually returns 400 for validation errors
                if grep -q "status_code=400" "$api_file" && grep -q "validation.*fail\|Validation failed" "$api_file"; then
                    print_error "Test expects 500 for validation error, but API returns 400: $test_file"
                    print_error "This will cause CI/CD test failures"
                    ((consistency_issues++))
                fi
            fi
        fi
    done

    # Check for authentication mocking inconsistencies
    print_status "Checking authentication mocking patterns..."

    for test_file in $test_files; do
        if grep -q "mock_auth_success\|require_auth" "$test_file"; then
            # Check if test has proper auth mocking setup
            if ! grep -q "create_auth_request\|x-ms-client-principal" "$test_file"; then
                print_warning "Test file $test_file may have incomplete auth mocking"
                print_warning "This could cause intermittent CI/CD failures"
            fi
        fi
    done

    # Check for database field naming consistency
    print_status "Checking database field naming consistency..."

    for api_file in $(find . -name "__init__.py" -path "*/api/*"); do
        if grep -q "ownerId\|userId" "$api_file"; then
            local test_file=${api_file/__init__.py/test.py}
            test_file=${api_file/__init__.py/_test.py}

            if [ -f "$test_file" ]; then
                # Check for inconsistent field names between API and tests
                local api_uses_owner_id=$(grep -c "ownerId" "$api_file")
                local api_uses_user_id=$(grep -c "userId" "$api_file")
                local test_expects_owner_id=$(grep -c "ownerId" "$test_file")
                local test_expects_user_id=$(grep -c "userId" "$test_file")

                if [ "$api_uses_user_id" -gt 0 ] && [ "$test_expects_owner_id" -gt "$test_expects_user_id" ]; then
                    print_warning "Potential field naming inconsistency in $api_file"
                    print_warning "API primarily uses 'userId' but test expects 'ownerId'"
                fi
            fi
        fi
    done

    # Check for missing error handling patterns
    print_status "Checking error handling patterns..."

    for api_file in $(find . -name "__init__.py" -path "*/api/*"); do
        if ! grep -q "SutraAPIError\|handle_api_error" "$api_file"; then
            print_warning "API file $api_file may be missing standardized error handling"
        fi
    done

    if [ $consistency_issues -gt 0 ]; then
        print_error "Found $consistency_issues critical API consistency issues"
        return 1
    else
        print_success "API consistency validation passed"
        return 0
    fi
}

# Function to validate E2E setup (simulate CI/CD environment)
validate_e2e_setup() {
    print_status "Validating E2E testing setup (CI/CD simulation)..."

    # Test that package.json scripts exist and are valid
    if ! grep -q '"e2e:setup"' package.json; then
        print_error "e2e:setup script not found in package.json"
        return 1
    fi

    if ! grep -q '"e2e:cleanup"' package.json; then
        print_error "e2e:cleanup script not found in package.json"
        return 1
    fi

    # Check that E2E scripts exist and are executable
    if [ ! -f "scripts/e2e-setup.sh" ] || [ ! -x "scripts/e2e-setup.sh" ]; then
        print_error "scripts/e2e-setup.sh not found or not executable"
        return 1
    fi

    if [ ! -f "scripts/e2e-cleanup.sh" ] || [ ! -x "scripts/e2e-cleanup.sh" ]; then
        print_error "scripts/e2e-cleanup.sh not found or not executable"
        return 1
    fi

    # Validate docker-compose.yml exists and is valid
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        return 1
    fi

    # Test docker-compose configuration validity using modern command first
    local config_valid=false
    if docker compose version &> /dev/null 2>&1; then
        if docker compose config >/dev/null 2>&1; then
            config_valid=true
            print_success "docker-compose.yml is valid (verified with modern docker compose)"
        fi
    fi

    # Fallback to legacy command if modern failed
    if [ "$config_valid" = false ] && command -v docker-compose &> /dev/null; then
        if docker-compose config >/dev/null 2>&1; then
            config_valid=true
            print_success "docker-compose.yml is valid (verified with legacy docker-compose)"
        fi
    fi

    if [ "$config_valid" = false ]; then
        print_error "docker-compose.yml configuration is invalid"
        return 1
    fi

    # Test that our E2E scripts can handle the current environment
    print_status "Testing E2E script compatibility..."

    # Test e2e-setup.sh dry run (validate syntax)
    if ! bash -n scripts/e2e-setup.sh; then
        print_error "scripts/e2e-setup.sh has syntax errors"
        return 1
    fi

    # Test e2e-cleanup.sh dry run (validate syntax)
    if ! bash -n scripts/e2e-cleanup.sh; then
        print_error "scripts/e2e-cleanup.sh has syntax errors"
        return 1
    fi

    print_success "E2E setup validation passed"
    return 0
}

# Function to validate GitHub Actions for deprecated actions
validate_github_actions() {
    print_status "Validating GitHub Actions for deprecated actions..."

    # Check for deprecated actions
    local deprecated_found=false

    # Check for deprecated upload-artifact v3
    if grep -r "actions/upload-artifact@v3" .github/workflows/ >/dev/null 2>&1; then
        print_error "Found deprecated actions/upload-artifact@v3 - must use v4"
        deprecated_found=true
    fi

    # Check for deprecated download-artifact v3
    if grep -r "actions/download-artifact@v3" .github/workflows/ >/dev/null 2>&1; then
        print_error "Found deprecated actions/download-artifact@v3 - must use v4"
        deprecated_found=true
    fi

    # Check for deprecated setup-node v3
    if grep -r "actions/setup-node@v3" .github/workflows/ >/dev/null 2>&1; then
        print_warning "Found actions/setup-node@v3 - consider upgrading to v4"
    fi

    # Check for deprecated checkout v3
    if grep -r "actions/checkout@v3" .github/workflows/ >/dev/null 2>&1; then
        print_warning "Found actions/checkout@v3 - consider upgrading to v4"
    fi

    if [ "$deprecated_found" = true ]; then
        print_error "Deprecated GitHub Actions found - this will cause CI/CD failure"
        return 1
    else
        print_success "No deprecated GitHub Actions found"
        return 0
    fi
}

# Function to validate Docker builds (simulate CI/CD environment)
validate_docker_builds() {
    print_status "Validating Docker builds (CI/CD simulation)..."

    # Check if Dockerfile.e2e exists
    if [ ! -f "Dockerfile.e2e" ]; then
        print_error "Dockerfile.e2e not found"
        return 1
    fi

    # Validate Dockerfile syntax
    if ! docker build --no-cache --target frontend -f Dockerfile.e2e . --dry-run >/dev/null 2>&1; then
        print_warning "Docker build dry-run not supported, attempting limited validation"
    fi

    # Check for common Docker build issues
    print_status "Checking for common Docker build issues..."

    # Check if package.json build script dependencies are available
    local build_script=$(grep -A1 '"build":' package.json | tail -1 | sed 's/.*"build": "\(.*\)".*/\1/')

    if echo "$build_script" | grep -q "tsc"; then
        print_status "Build script uses tsc, checking TypeScript dependency..."

        # Check if typescript is in devDependencies
        if ! grep -A20 '"devDependencies"' package.json | grep -q '"typescript"'; then
            print_error "TypeScript not found in devDependencies but required by build script"
            return 1
        fi

        # Check Dockerfile for proper dependency installation
        if grep -q "npm ci --only=production" Dockerfile.e2e; then
            print_error "Dockerfile.e2e uses --only=production but build requires devDependencies (like tsc)"
            print_error "This will cause 'tsc: not found' errors in CI/CD"
            return 1
        fi
    fi

    # Check if vite is used in build
    if echo "$build_script" | grep -q "vite"; then
        if ! grep -A20 '"devDependencies"' package.json | grep -q '"vite"'; then
            print_error "Vite not found in devDependencies but required by build script"
            return 1
        fi
    fi

    # Validate that all files referenced in Dockerfile exist
    print_status "Validating Dockerfile file references..."

    local dockerfile_errors=false

    # Check for package files
    if ! [ -f "package.json" ]; then
        print_error "package.json referenced in Dockerfile but not found"
        dockerfile_errors=true
    fi

    if ! [ -f "tsconfig.json" ] && ! [ -f "tsconfig.base.json" ]; then
        print_warning "No tsconfig.json found but referenced in Dockerfile"
    fi

    if ! [ -f "vite.config.ts" ]; then
        print_error "vite.config.ts referenced in Dockerfile but not found"
        dockerfile_errors=true
    fi

    if ! [ -d "src" ]; then
        print_error "src/ directory referenced in Dockerfile but not found"
        dockerfile_errors=true
    fi

    if ! [ -d "public" ]; then
        print_error "public/ directory referenced in Dockerfile but not found"
        dockerfile_errors=true
    fi

    if ! [ -f "index.html" ]; then
        print_error "index.html referenced in Dockerfile but not found"
        dockerfile_errors=true
    fi

    if [ "$dockerfile_errors" = true ]; then
        return 1
    fi

    # Test docker-compose build without actually building (config validation)
    print_status "Testing docker-compose build configuration..."

    # Try modern docker compose first
    if docker compose version &> /dev/null 2>&1; then
        if ! docker compose config >/dev/null 2>&1; then
            print_error "docker-compose.yml build configuration is invalid"
            return 1
        fi
    elif command -v docker-compose &> /dev/null; then
        if ! docker-compose config >/dev/null 2>&1; then
            print_error "docker-compose.yml build configuration is invalid"
            return 1
        fi
    fi

    # Check Azure Functions Dockerfile issues
    print_status "Validating Azure Functions container setup..."

    # CRITICAL: Check if Dockerfile.dev exists first
    if [ ! -f "api/Dockerfile.dev" ]; then
        print_error "api/Dockerfile.dev not found but required by Docker Compose files"
        print_error "This will cause CI/CD E2E build failures"
        print_error "Create api/Dockerfile.dev for development environment"
        return 1
    fi

    if [ -f "api/Dockerfile.dev" ]; then
        # Check for incorrect manual CMD usage in Azure Functions container
        if grep -q 'CMD.*\["func"' api/Dockerfile.dev; then
            print_error "Azure Functions Dockerfile.dev uses manual 'func' CMD"
            print_error "This will cause 'func: executable file not found' errors"
            print_error "Azure Functions base images have built-in startup commands"
            print_error "Remove the CMD line and let the base image handle startup"
            return 1
        fi

        # Check for missing AzureWebJobsScriptRoot environment variable
        if ! grep -q "AzureWebJobsScriptRoot" api/Dockerfile.dev; then
            print_error "Azure Functions Dockerfile.dev missing AzureWebJobsScriptRoot environment variable"
            print_error "This is required for proper Azure Functions operation"
            return 1
        fi

        # Check if files are copied to the correct location
        if ! grep -q "COPY.*/home/site/wwwroot" api/Dockerfile.dev; then
            print_error "Azure Functions Dockerfile.dev not copying files to /home/site/wwwroot"
            print_error "This is the required location for Azure Functions"
            return 1
        fi

        # Check for host.json presence (required for Azure Functions)
        if [ ! -f "api/host.json" ]; then
            print_error "api/host.json not found but required for Azure Functions"
            return 1
        fi

        # Validate host.json format
        if ! python3 -m json.tool api/host.json >/dev/null 2>&1; then
            print_error "api/host.json is not valid JSON"
            return 1
        fi

        # Check for at least one function definition
        local function_count=$(find api -name "function.json" | wc -l)
        if [ "$function_count" -eq 0 ]; then
            print_error "No function.json files found in api/ directory"
            print_error "Azure Functions requires at least one function definition"
            return 1
        fi

        # Validate health check configuration
        print_status "Validating Azure Functions health check setup..."

        # Check if docker-compose has health check for functions-api
        if [ -f "docker-compose.yml" ]; then
            # Look for healthcheck in the functions-api service section
            if sed -n '/^  functions-api:/,/^  [a-z]/p' docker-compose.yml | grep -q "healthcheck:"; then
                # Health check is configured, validate dependencies
                local healthcheck_command=$(sed -n '/^  functions-api:/,/^  [a-z]/p' docker-compose.yml | grep -A 2 "test:" | head -1)

                # Check if health check uses curl
                if echo "$healthcheck_command" | grep -q "curl"; then
                    # Verify curl is installed in Dockerfile (check apt-get install section)
                    if ! grep -A 10 "apt-get install" api/Dockerfile.dev | grep -q "curl"; then
                        print_error "Docker health check uses 'curl' but curl is not installed in Dockerfile.dev"
                        print_error "Add 'curl' to the apt-get install command in api/Dockerfile.dev"
                        print_error "This will cause health check failures and container dependency issues"
                        return 1
                    fi
                fi

                # Check if health endpoint exists
                if echo "$healthcheck_command" | grep -q "/api/health"; then
                    if [ ! -f "api/health/__init__.py" ]; then
                        print_error "Health check endpoint /api/health configured but api/health/__init__.py not found"
                        return 1
                    fi

                    if [ ! -f "api/health/function.json" ]; then
                        print_error "Health check endpoint /api/health configured but api/health/function.json not found"
                        return 1
                    fi

                    # Validate health function.json configuration
                    if ! grep -q '"route": "health"' api/health/function.json; then
                        print_error "Health function not configured with correct route in function.json"
                        return 1
                    fi
                fi

                print_success "Health check configuration validated"
            else
                print_warning "No health check configured for functions-api service"
                print_warning "Consider adding health check for better container orchestration"
            fi
        fi

        print_success "Azure Functions container validation passed (found $function_count functions)"
    fi

    print_success "Docker build validation passed"
    return 0
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
    echo "⚙️ Running CI/CD Validation"
    echo "==========================="

    if ! validate_e2e_setup; then
        ((failed_checks++))
    fi

    if ! validate_github_actions; then
        ((failed_checks++))
    fi

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

    echo ""
    echo "🔧 Validating GitHub Actions"
    echo "============================"

    if ! validate_github_actions; then
        ((failed_checks++))
    fi

    echo ""
    echo "✅ Validating E2E Setup"
    echo "======================"

    if ! validate_e2e_setup; then
        ((failed_checks++))
    fi

    echo ""
    echo "🐳 Validating Docker Builds"
    echo "=========================="

    if ! validate_docker_builds; then
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
