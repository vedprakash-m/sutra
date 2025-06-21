#!/bin/bash

# Test script specifically for health check curl dependency validation

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

# Test health check validation by temporarily removing curl
test_health_check_validation() {
    print_status "Testing health check curl dependency validation..."

    # Create a backup of the current Dockerfile
    cp api/Dockerfile.dev api/Dockerfile.dev.backup

    # Create a version without curl but with proper Azure Functions setup
    cat > api/Dockerfile.dev << 'EOF'
# Development container for Azure Functions
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

# Set Azure Functions environment variables
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# Install system dependencies for potential compilation needs (MISSING curl)
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements-minimal.txt requirements-ci.txt requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy function code
COPY . /home/site/wwwroot
EOF

    echo ""
    print_status "Testing validation with missing curl dependency..."

    # Run the health check validation
    if [ -f "docker-compose.yml" ]; then
        # Look for healthcheck in the functions-api service section
        if sed -n '/^  functions-api:/,/^  [a-z]/p' docker-compose.yml | grep -q "healthcheck:"; then
            # Health check is configured, validate dependencies
            local healthcheck_command=$(sed -n '/^  functions-api:/,/^  [a-z]/p' docker-compose.yml | grep -A 2 "test:" | head -1)

            # Check if health check uses curl
            if echo "$healthcheck_command" | grep -q "curl"; then
                # Verify curl is installed in Dockerfile
                if ! grep -q "curl" api/Dockerfile.dev; then
                    print_success "Validation correctly detected missing curl dependency!"
                    print_error "Docker health check uses 'curl' but curl is not installed in Dockerfile.dev"
                    print_error "Add 'curl' to the apt-get install command in api/Dockerfile.dev"
                    print_error "This will cause health check failures and container dependency issues"

                    # Restore the backup
                    mv api/Dockerfile.dev.backup api/Dockerfile.dev
                    return 0  # This is expected to fail, so return success
                fi
            fi
        fi
    fi

    print_error "Validation should have failed but didn't!"
    # Restore the backup
    mv api/Dockerfile.dev.backup api/Dockerfile.dev
    return 1
}

# Main test execution
main() {
    echo "🧪 Testing Health Check Curl Dependency Validation"
    echo "=================================================="

    if test_health_check_validation; then
        print_success "Health check curl dependency validation works correctly!"
        echo ""
        echo "Summary:"
        echo "- ✅ Validation detects missing curl dependency for health checks"
        echo "- ✅ Provides clear error message with fix guidance"
        echo "- ✅ Prevents health check failures in CI/CD"
    else
        print_error "Health check curl dependency validation failed"
        exit 1
    fi
}

# Run the test
main "$@"
