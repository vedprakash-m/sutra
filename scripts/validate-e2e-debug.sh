#!/bin/bash

# Debug E2E Validation Script
# Captures detailed logs and runs containers interactively

set -e

echo "🔍 DEBUG E2E VALIDATION"
echo "======================="
echo "Debugging Azure Functions container startup issues"
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

# Clean up function
cleanup() {
    log_info "Cleaning up containers..."
    docker stop sutra-functions-debug 2>/dev/null || true
    docker rm sutra-functions-debug 2>/dev/null || true
    docker-compose down -v 2>/dev/null || true
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Check Docker
check_docker() {
    log_info "Checking Docker availability..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    log_success "Docker is available"
}

# Build container
build_container() {
    log_info "Building Functions API container..."
    docker-compose down -v 2>/dev/null || true

    if ! docker-compose build functions-api; then
        log_error "Functions API build failed"
        exit 1
    fi
    log_success "Functions API built successfully"
}

# Start dependencies
start_dependencies() {
    log_info "Starting minimal dependencies..."
    docker-compose up -d azurite
    sleep 3
    log_success "Azurite started"
}

# Test container startup with debug
test_container_startup() {
    log_info "Testing Functions API container startup with debugging..."

    # Start container and capture immediate logs
    docker run --rm -d \
        --name sutra-functions-debug \
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

    log_info "Container started, waiting 5 seconds for initial startup..."
    sleep 5

    # Check if container is still running
    if docker ps | grep -q "sutra-functions-debug"; then
        log_success "Container is still running"

        # Get logs immediately
        log_info "Getting container logs..."
        docker logs sutra-functions-debug 2>&1 | head -50

        # Wait for actual startup
        log_info "Waiting for Functions runtime to fully initialize..."
        local max_attempts=20
        local attempt=0

        while [ $attempt -lt $max_attempts ]; do
            # Check container status
            if ! docker ps | grep -q "sutra-functions-debug"; then
                log_error "Container stopped running unexpectedly"
                log_error "Final container logs:"
                docker logs sutra-functions-debug 2>&1 || true
                return 1
            fi

            # Check if health endpoint is available
            if curl -f http://localhost:7071/api/health --max-time 3 >/dev/null 2>&1; then
                log_success "Health endpoint is responding!"

                # Get actual response
                local health_response
                health_response=$(curl -s http://localhost:7071/api/health)
                log_success "Health response: $health_response"
                return 0
            fi

            sleep 3
            attempt=$((attempt + 1))
            log_info "Health check attempt ${attempt}/${max_attempts}..."
        done

        log_warning "Health endpoint did not respond within timeout"
        log_info "Final container logs:"
        docker logs sutra-functions-debug 2>&1 | tail -30

        # Try to see what's listening on port 7071
        log_info "Checking what's listening inside container..."
        docker exec sutra-functions-debug sh -c "netstat -tlnp 2>/dev/null || ss -tlnp 2>/dev/null || echo 'No network tools available'" || true

        return 1

    else
        log_error "Container stopped immediately after startup"
        log_error "Container logs:"
        docker logs sutra-functions-debug 2>&1 || true
        return 1
    fi
}

# Test functions manually
test_functions_manually() {
    log_info "Testing function import manually..."

    docker run --rm -it \
        --network sutra_sutra-network \
        -e AzureWebJobsStorage="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;" \
        -e FUNCTIONS_WORKER_RUNTIME=python \
        -e ENVIRONMENT=test \
        sutra-functions-api:latest \
        python3 -c "
import sys
sys.path.append('/home/site/wwwroot')
try:
    from health import main
    print('✅ Health function can be imported')
    print(f'Function: {main}')
except Exception as e:
    print(f'❌ Health function import failed: {e}')
    import traceback
    traceback.print_exc()
"
}

# Main execution
main() {
    log_info "Starting Debug E2E Validation..."

    check_docker
    build_container
    start_dependencies

    if test_container_startup; then
        log_success "🎉 Container startup successful!"
    else
        log_warning "Container startup failed, trying manual function test..."
        test_functions_manually
    fi

    echo ""
    log_info "Debug validation completed"
}

main "$@"
