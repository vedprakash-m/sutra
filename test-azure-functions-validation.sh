#!/bin/bash

# Test script for Azure Functions Docker validation
# This tests the specific Azure Functions container validation logic

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Test Azure Functions validation logic
test_azure_functions_validation() {
    print_status "Testing Azure Functions container validation..."

    # Check Azure Functions Dockerfile issues
    print_status "Validating Azure Functions container setup..."

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
                    # Verify curl is installed in Dockerfile
                    if ! grep -q "curl" api/Dockerfile.dev; then
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
    else
        print_warning "api/Dockerfile.dev not found, skipping Azure Functions validation"
    fi

    return 0
}

# Simulate the problem (temporarily revert to problematic Dockerfile)
test_with_problem() {
    print_status "Testing validation with problematic Dockerfile..."

    # Create a backup of the current Dockerfile
    cp api/Dockerfile.dev api/Dockerfile.dev.backup

    # Create a problematic version (with manual CMD and missing curl)
    cat > api/Dockerfile.dev << 'EOF'
# Development container for Azure Functions
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

# Install system dependencies for potential compilation needs (MISSING curl)
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /home/site/wwwroot

# Copy requirements and install dependencies
COPY requirements-minimal.txt requirements-ci.txt requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy function code
COPY . .

# Expose port
EXPOSE 7071

# Start Azure Functions runtime (PROBLEMATIC LINE)
CMD ["func", "host", "start", "--cors", "*"]
EOF

    echo ""
    print_status "Testing validation with problematic CMD line..."
    if test_azure_functions_validation; then
        print_error "Validation should have failed but didn't!"
        # Restore the backup
        mv api/Dockerfile.dev.backup api/Dockerfile.dev
        return 1
    else
        print_success "Validation correctly detected the problematic CMD line"
    fi

    # Restore the backup
    mv api/Dockerfile.dev.backup api/Dockerfile.dev
    return 0
}

# Test with the fixed version
test_with_fix() {
    print_status "Testing validation with fixed Dockerfile..."

    echo ""
    if test_azure_functions_validation; then
        print_success "Validation passed with fixed Dockerfile"
        return 0
    else
        print_error "Validation failed even with fixed Dockerfile!"
        return 1
    fi
}

# Main test execution
main() {
    echo "🧪 Testing Azure Functions Container Validation"
    echo "==============================================="

    # Test 1: Check current state (should pass after fix)
    if ! test_with_fix; then
        print_error "Test with fix failed"
        exit 1
    fi

    echo ""

    # Test 2: Check with problematic version (should fail)
    if ! test_with_problem; then
        print_error "Test with problem simulation failed"
        exit 1
    fi

    echo ""
    print_success "All Azure Functions validation tests passed!"
    echo ""
    echo "Summary:"
    echo "- ✅ Validation detects manual 'func' CMD usage (causes runtime errors)"
    echo "- ✅ Validation ensures proper Azure Functions environment setup"
    echo "- ✅ Validation checks for required configuration files"
    echo "- ✅ Fixed Dockerfile passes validation"
}

# Run the tests
main "$@"
