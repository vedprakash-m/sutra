#!/bin/bash

# CI-Mirror E2E Validation Script
# This exactly mirrors the CI/CD flow to catch issues locally

set -e

echo "🎯 CI-MIRROR E2E VALIDATION"
echo "============================"
echo "This validation exactly mirrors the CI/CD environment"
echo ""

# Ensure we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must be run from the project root directory"
    exit 1
fi

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

# Function to check if Docker is available
check_docker() {
    log_info "Checking Docker availability..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running - start Docker Desktop first"
        exit 1
    fi
    log_success "Docker is available"
}

# Function to validate docker-compose.yml syntax
validate_docker_compose() {
    log_info "Validating docker-compose.yml syntax..."

    if ! docker-compose config >/dev/null 2>&1; then
        log_error "docker-compose.yml has syntax errors!"
        log_error "Running docker-compose config to show errors:"
        docker-compose config
        exit 1
    fi

    log_success "docker-compose.yml syntax is valid"
}

# Function to check required files
check_required_files() {
    log_info "Checking required files..."

    local files=(
        "docker-compose.yml"
        "api/Dockerfile.dev"
        "Dockerfile.e2e"
        "api/health/__init__.py"
        "api/health/function.json"
        "api/host.json"
    )

    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done

    log_success "All required files present"
}

# Function to clean up existing containers
cleanup_containers() {
    log_info "Cleaning up existing containers..."
    docker-compose down -v 2>/dev/null || true
    docker system prune -f >/dev/null 2>&1 || true
    log_success "Cleanup completed"
}

# Custom timeout function for macOS compatibility
run_with_timeout() {
    local timeout_duration=$1
    shift
    local cmd="$@"

    # Run command in background
    $cmd &
    local cmd_pid=$!

    # Wait for timeout or completion
    local count=0
    while [ $count -lt $timeout_duration ]; do
        if ! kill -0 $cmd_pid 2>/dev/null; then
            # Process finished
            wait $cmd_pid
            return $?
        fi
        sleep 1
        count=$((count + 1))
    done

    # Timeout reached
    kill $cmd_pid 2>/dev/null
    return 124
}

# Function to test the exact CI flow
test_ci_flow() {
    log_info "Testing exact CI flow..."

    # Step 1: Build all containers (like CI does)
    log_info "Building all containers..."
    if ! docker-compose build --no-cache; then
        log_error "Container build failed"
        exit 1
    fi
    log_success "All containers built successfully"

    # Step 2: Start services with dependency chain (like CI does)
    log_info "Starting services with full dependency chain..."

    # Start in background and capture output
    if ! run_with_timeout 300 docker-compose up -d; then
        log_error "Services failed to start within 5 minutes"
        log_error "Showing container logs for debugging:"
        docker-compose logs
        exit 1
    fi

    # Step 3: Wait for services to be ready (like CI does)
    log_info "Waiting for services to be ready..."

    local max_wait=180
    local wait_time=0

    while [ $wait_time -lt $max_wait ]; do
        # Check if functions-api is healthy
        if docker inspect sutra-functions-api --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            log_success "Functions API container is healthy"
            break
        fi

        if docker inspect sutra-functions-api --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "unhealthy"; then
            log_error "Functions API container is unhealthy"
            log_error "Container logs:"
            docker-compose logs functions-api
            log_error "Container health status:"
            docker inspect sutra-functions-api --format='{{json .State.Health}}'
            exit 1
        fi

        sleep 5
        wait_time=$((wait_time + 5))
        log_info "Waiting for health check... (${wait_time}s/${max_wait}s)"
    done

    if [ $wait_time -ge $max_wait ]; then
        log_error "Services did not become healthy within timeout"
        log_error "Current container status:"
        docker-compose ps
        log_error "Container logs:"
        docker-compose logs
        exit 1
    fi
}

# Function to test health endpoints
test_health_endpoints() {
    log_info "Testing health endpoints..."

    # Test Functions API health endpoint
    log_info "Testing Functions API health endpoint..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:7071/api/health --max-time 5 >/dev/null 2>&1; then
            log_success "Functions API health endpoint is responding"
            break
        fi

        sleep 2
        attempt=$((attempt + 1))
        log_info "Health endpoint attempt ${attempt}/${max_attempts}..."
    done

    if [ $attempt -ge $max_attempts ]; then
        log_error "Functions API health endpoint is not responding"
        log_error "Container logs:"
        docker-compose logs functions-api
        exit 1
    fi

    # Test actual health response
    log_info "Testing health response content..."
    local health_response
    health_response=$(curl -s http://localhost:7071/api/health)

    if echo "$health_response" | grep -q '"status":"healthy"'; then
        log_success "Health endpoint returns healthy status"
    else
        log_error "Health endpoint response unexpected: $health_response"
        exit 1
    fi
}

# Function to test container dependencies
test_container_dependencies() {
    log_info "Testing container dependencies..."

    # Check if all expected containers are running
    local expected_containers=(
        "sutra-cosmos-emulator"
        "sutra-azurite"
        "sutra-functions-api"
        "sutra-frontend"
    )

    for container in "${expected_containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_success "Container $container is running"
        else
            log_error "Container $container is not running"
            exit 1
        fi
    done

    # Check if frontend can connect to functions-api
    log_info "Testing frontend to functions-api connectivity..."
    if docker exec sutra-frontend sh -c "curl -f http://functions-api:7071/api/health --max-time 5" >/dev/null 2>&1; then
        log_success "Frontend can connect to Functions API"
    else
        log_error "Frontend cannot connect to Functions API"
        exit 1
    fi
}

# Function to run performance tests
test_performance() {
    log_info "Testing performance characteristics..."

    # Test response time
    local response_time
    response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:7071/api/health)

    # Convert to milliseconds
    local response_ms
    response_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)

    if [ "$response_ms" -lt 2000 ]; then
        log_success "Response time: ${response_ms}ms (< 2000ms)"
    else
        log_warning "Response time: ${response_ms}ms (>= 2000ms) - may indicate performance issues"
    fi
}

# Function to run frontend tests with coverage (mirrors CI exactly)
test_frontend_coverage() {
    log_info "Running frontend tests with coverage (CI mirror)..."

    if ! npm run test:coverage; then
        log_error "Frontend tests failed coverage thresholds"
        log_error "CI expects 70% coverage for statements, branches, and lines"
        return 1
    fi

    log_success "Frontend tests passed with required coverage"
}

# Function to run backend tests (mirrors CI exactly)
test_backend_comprehensive() {
    log_info "Running comprehensive backend tests (CI mirror)..."

    cd api

    # Run with verbose output and coverage like CI does
    if ! python -m pytest --tb=short -v --cov=. --cov-report=term-missing; then
        log_error "Backend tests failed"
        cd ..
        return 1
    fi

    cd ..
    log_success "Backend tests passed"
}

# Function to validate test results match CI expectations
validate_ci_expectations() {
    log_info "Validating test results match CI expectations..."

    # Check frontend coverage
    log_info "Checking frontend coverage meets CI thresholds..."
    if ! test_frontend_coverage; then
        log_error "Frontend coverage validation failed"
        return 1
    fi

    # Check backend tests
    log_info "Checking backend tests comprehensive..."
    if ! test_backend_comprehensive; then
        log_error "Backend test validation failed"
        return 1
    fi

    log_success "All CI expectations validated"
}

# Function to generate validation report
generate_report() {
    log_info "Generating validation report..."

    cat > CI_MIRROR_VALIDATION_REPORT.md << EOF
# CI-Mirror Validation Report

**Date:** $(date)
**Status:** ✅ PASSED
**Environment:** Local (mirroring CI/CD)

## Test Results

### Container Status
$(docker-compose ps)

### Health Check Results
- Functions API Health: ✅ PASSED
- Container Dependencies: ✅ PASSED
- Service Connectivity: ✅ PASSED

### Performance Metrics
- Health Endpoint Response: Available
- Container Startup: Successful
- Dependency Chain: Working

## Summary
All CI-mirror validation tests passed successfully. The application is ready for CI/CD deployment.
EOF

    log_success "Report generated: CI_MIRROR_VALIDATION_REPORT.md"
}

# Main execution
main() {
    echo ""
    log_info "Starting CI-Mirror E2E Validation..."

    # Pre-flight checks
    check_docker
    validate_docker_compose
    check_required_files

    # Clean slate
    cleanup_containers

    # Core validation (mirrors CI exactly)
    test_ci_flow
    test_health_endpoints
    test_container_dependencies
    test_performance

    # NEW: Validate comprehensive tests like CI does
    validate_ci_expectations

    # Generate report
    generate_report

    # Cleanup
    cleanup_containers

    echo ""
    log_success "🎉 CI-MIRROR VALIDATION COMPLETED SUCCESSFULLY!"
    echo ""
    log_success "✅ All tests passed - Ready for CI/CD deployment"
    log_info "📋 Report available: CI_MIRROR_VALIDATION_REPORT.md"
    echo ""
}

# Run main function
main "$@"
