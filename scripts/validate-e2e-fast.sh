#!/bin/bash

# Fast E2E Validation Script
# Focuses on core issues without full dependency chain

set -e

echo "🚀 FAST E2E VALIDATION"
echo "======================"
echo "Testing core functionality without full CI dependency chain"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Docker
check_docker() {
    log_info "Checking Docker availability..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    log_success "Docker is available"
}

# Validate docker-compose syntax
validate_compose_syntax() {
    log_info "Validating docker-compose.yml syntax..."
    if ! docker-compose config >/dev/null 2>&1; then
        log_error "docker-compose.yml has syntax errors!"
        docker-compose config
        exit 1
    fi
    log_success "docker-compose.yml syntax is valid"
}

# Test functions API container independently
test_functions_api_standalone() {
    log_info "Testing Functions API container standalone..."

    # Cleanup
    docker-compose down -v 2>/dev/null || true

    # Build only functions-api
    log_info "Building Functions API container..."
    if ! docker-compose build functions-api; then
        log_error "Functions API build failed"
        exit 1
    fi
    log_success "Functions API built successfully"

    # Start minimal dependencies
    log_info "Starting minimal dependencies..."
    docker-compose up -d azurite
    sleep 5

    # Start Functions API with minimal environment
    log_info "Starting Functions API container..."
    docker run --rm -d \
        --name sutra-functions-test \
        --network sutra_sutra-network \
        -p 7071:7071 \
        -e AzureWebJobsStorage="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;" \
        -e FUNCTIONS_WORKER_RUNTIME=python \
        -e ENVIRONMENT=test \
        -e COSMOS_DB_ENDPOINT=test://localhost \
        -e COSMOS_DB_KEY=test-key \
        -e WEBSITES_INCLUDE_CLOUD_CERTS=true \
        -e AZURE_FUNCTIONS_ENVIRONMENT=Development \
        -e AzureWebJobsScriptRoot=/home/site/wwwroot \
        -e AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
        sutra-functions-api:latest

    # Wait for startup
    log_info "Waiting for Functions API to start..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:7071/api/health --max-time 5 >/dev/null 2>&1; then
            log_success "Functions API health endpoint is responding"
            break
        fi
        sleep 2
        attempt=$((attempt + 1))
        log_info "Startup check ${attempt}/${max_attempts}..."
    done

    if [ $attempt -ge $max_attempts ]; then
        log_error "Functions API failed to start properly"
        log_error "Container logs:"
        docker logs sutra-functions-test 2>&1 | tail -20
        docker stop sutra-functions-test >/dev/null 2>&1 || true
        docker-compose down -v >/dev/null 2>&1 || true
        exit 1
    fi

    # Test health response
    log_info "Testing health response content..."
    local health_response
    health_response=$(curl -s http://localhost:7071/api/health)

    if echo "$health_response" | grep -q '"status":"healthy"'; then
        log_success "Health endpoint returns healthy status"
        log_info "Health response: $health_response"
    else
        log_error "Health endpoint response unexpected: $health_response"
        docker stop sutra-functions-test >/dev/null 2>&1 || true
        docker-compose down -v >/dev/null 2>&1 || true
        exit 1
    fi

    # Cleanup
    docker stop sutra-functions-test >/dev/null 2>&1 || true
    docker-compose down -v >/dev/null 2>&1 || true

    log_success "Functions API standalone test passed"
}

# Test docker-compose health check configuration
test_healthcheck_config() {
    log_info "Testing health check configuration..."

    # Check if health check is properly configured
    local healthcheck_test
    healthcheck_test=$(docker-compose config | grep -A 10 "healthcheck:" | grep "test:" | head -1)

    if echo "$healthcheck_test" | grep -q "curl"; then
        log_success "Health check uses curl (correct)"
    else
        log_warning "Health check might not use curl properly"
    fi

    # Verify health endpoint exists
    if [ -f "api/health/__init__.py" ] && [ -f "api/health/function.json" ]; then
        log_success "Health endpoint files exist"
    else
        log_error "Health endpoint files missing"
        exit 1
    fi
}

# Main execution
main() {
    log_info "Starting Fast E2E Validation..."

    check_docker
    validate_compose_syntax
    test_healthcheck_config
    test_functions_api_standalone

    echo ""
    log_success "🎉 FAST E2E VALIDATION COMPLETED SUCCESSFULLY!"
    echo ""
    log_success "✅ Functions API container works correctly"
    log_success "✅ Health endpoint is responding"
    log_success "✅ Ready for full CI validation"
    echo ""
}

main "$@"
