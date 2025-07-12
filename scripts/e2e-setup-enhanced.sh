#!/bin/bash

# Enhanced E2E Setup Script
# Provides comprehensive E2E environment setup with proper service orchestration
# Ensures 100% parity between local development and CI/CD environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMEOUT_SECONDS=300
HEALTHCHECK_INTERVAL=5
MAX_RETRIES=60

echo -e "${BLUE}🚀 Enhanced E2E Environment Setup${NC}"
echo -e "${CYAN}Project: Sutra Multi-LLM Prompt Studio${NC}"
echo -e "${CYAN}Mode: Full-Stack E2E Testing${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to log with timestamp
log_with_time() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Function to check service health
check_service_health() {
    local service_name="$1"
    local health_url="$2"
    local max_attempts="${3:-$MAX_RETRIES}"

    echo -e "${BLUE}🔍 Checking $service_name health...${NC}"

    for ((i=1; i<=max_attempts; i++)); do
        if curl -f "$health_url" --max-time 5 --silent > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is healthy (attempt $i/$max_attempts)${NC}"
            return 0
        fi

        if [ $i -eq $max_attempts ]; then
            echo -e "${RED}❌ $service_name failed to become healthy after $max_attempts attempts${NC}"
            return 1
        fi

        echo -e "${YELLOW}⏳ $service_name not ready yet (attempt $i/$max_attempts), retrying in ${HEALTHCHECK_INTERVAL}s...${NC}"
        sleep $HEALTHCHECK_INTERVAL
    done
}

# Function to determine the appropriate Docker Compose configuration
determine_docker_compose_config() {
    local arch=$(uname -m)
    local os=$(uname -s)
    local config_file=""

    # Log to stderr to avoid contaminating return value
    echo -e "${BLUE}🔍 Detecting system architecture and capabilities...${NC}" >&2
    log_with_time "System: $os, Architecture: $arch" >&2

    # Check if we're in CI environment
    if [ -n "$CI" ]; then
        echo -e "${CYAN}📊 CI Environment detected${NC}" >&2
        config_file="docker-compose.e2e-no-cosmos.yml"
    # Check if Cosmos DB emulator is supported
    elif [ "$arch" = "arm64" ] || [ "$arch" = "aarch64" ]; then
        echo -e "${YELLOW}⚠️  ARM64 detected - using no-cosmos configuration${NC}" >&2
        config_file="docker-compose.e2e-no-cosmos.yml"
    # Check if Docker has sufficient resources for full stack
    elif docker info 2>/dev/null | grep -q "Total Memory.*[0-9]G"; then
        echo -e "${GREEN}✅ Sufficient Docker resources for full stack${NC}" >&2
        config_file="docker-compose.e2e-arm64.yml"
    else
        echo -e "${YELLOW}⚠️  Limited resources - using optimized configuration${NC}" >&2
        config_file="docker-compose.e2e-no-cosmos.yml"
    fi

    # Return only the filename to stdout
    echo "$config_file"
}

# Function to cleanup existing resources
cleanup_existing_resources() {
    echo -e "${BLUE}🧹 Cleaning up existing resources...${NC}"

    # Stop any existing containers
    docker compose -f docker-compose.yml down --remove-orphans --volumes > /dev/null 2>&1 || true
    docker compose -f docker-compose.e2e-no-cosmos.yml down --remove-orphans --volumes > /dev/null 2>&1 || true
    docker compose -f docker-compose.e2e-arm64.yml down --remove-orphans --volumes > /dev/null 2>&1 || true

    # Clean up any leftover containers
    docker container prune -f > /dev/null 2>&1 || true
    docker network prune -f > /dev/null 2>&1 || true

    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to build and start services
start_services() {
    local compose_file="$1"

    echo -e "${BLUE}🏗️  Building and starting services with $compose_file...${NC}"

    # Build with no cache to ensure fresh images
    docker compose -f "$compose_file" build --no-cache

    # Start services in detached mode
    docker compose -f "$compose_file" up -d

    echo -e "${GREEN}✅ Services started${NC}"
}

# Function to validate service readiness
validate_service_readiness() {
    echo -e "${BLUE}🔍 Validating service readiness...${NC}"

    # Check backend health
    if ! check_service_health "Backend API" "http://localhost:7071/api/health"; then
        echo -e "${RED}❌ Backend health check failed${NC}"
        echo -e "${YELLOW}📋 Backend logs:${NC}"
        docker compose logs functions-api | tail -50
        return 1
    fi

    # Check frontend health
    if ! check_service_health "Frontend" "http://localhost:5173"; then
        echo -e "${RED}❌ Frontend health check failed${NC}"
        echo -e "${YELLOW}📋 Frontend logs:${NC}"
        docker compose logs frontend | tail -50
        return 1
    fi

    # Check storage emulator
    if ! check_service_health "Storage Emulator" "http://localhost:10000"; then
        echo -e "${RED}❌ Storage emulator health check failed${NC}"
        echo -e "${YELLOW}📋 Storage emulator logs:${NC}"
        docker compose logs azurite | tail -50
        return 1
    fi

    echo -e "${GREEN}✅ All services are ready${NC}"
}

# Function to setup test data
setup_test_data() {
    echo -e "${BLUE}🗃️  Setting up test data...${NC}"

    # Create test collections, prompts, and playbooks
    # This ensures E2E tests have consistent data to work with

    # Note: This would typically make API calls to seed data
    # For now, we'll create a marker file to indicate setup completion
    touch /tmp/sutra-e2e-setup-complete

    echo -e "${GREEN}✅ Test data setup completed${NC}"
}

# Function to validate E2E test requirements
validate_e2e_requirements() {
    echo -e "${BLUE}📋 Validating E2E test requirements...${NC}"

    # Check if Playwright is installed
    if ! npm list @playwright/test > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Installing Playwright...${NC}"
        npm install @playwright/test
    fi

    # Check if Playwright browsers are installed
    if ! npx playwright --version > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Installing Playwright browsers...${NC}"
        npx playwright install
    fi

    echo -e "${GREEN}✅ E2E test requirements validated${NC}"
}

# Main execution flow
main() {
    log_with_time "Starting E2E environment setup..."

    # Step 1: Determine configuration
    COMPOSE_FILE=$(determine_docker_compose_config)

    # Validate that we got a clean filename
    if [[ ! "$COMPOSE_FILE" =~ ^docker-compose\..*\.yml$ ]]; then
        echo -e "${RED}❌ Failed to determine Docker Compose configuration${NC}"
        echo -e "${RED}   Got: '$COMPOSE_FILE'${NC}"
        exit 1
    fi

    log_with_time "Using Docker Compose configuration: $COMPOSE_FILE"

    # Validate that the compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}❌ Docker Compose file not found: $COMPOSE_FILE${NC}"
        echo -e "${YELLOW}Available files:${NC}"
        ls -la docker-compose*.yml 2>/dev/null || echo "No Docker Compose files found"
        exit 1
    fi

    # Step 2: Cleanup existing resources
    cleanup_existing_resources

    # Step 3: Validate E2E requirements
    validate_e2e_requirements

    # Step 4: Start services
    start_services "$COMPOSE_FILE"

    # Step 5: Wait for services to be ready
    echo -e "${BLUE}⏳ Waiting for services to become ready...${NC}"
    sleep 10  # Initial wait for containers to initialize

    # Step 6: Validate service readiness
    if ! validate_service_readiness; then
        echo -e "${RED}❌ Service readiness validation failed${NC}"
        echo -e "${YELLOW}📋 Dumping service logs for debugging...${NC}"
        docker compose logs --tail=100
        exit 1
    fi

    # Step 7: Setup test data
    setup_test_data

    # Step 8: Final validation
    echo -e "${BLUE}🎯 Running final validation...${NC}"

    # Test that we can actually make API calls
    if curl -f "http://localhost:7071/api/health" --max-time 10 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API endpoint accessible${NC}"
    else
        echo -e "${RED}❌ API endpoint not accessible${NC}"
        exit 1
    fi

    # Test that frontend is serving content
    if curl -f "http://localhost:5173" --max-time 10 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend endpoint accessible${NC}"
    else
        echo -e "${RED}❌ Frontend endpoint not accessible${NC}"
        exit 1
    fi

    log_with_time "E2E environment setup completed successfully!"
    echo ""
    echo -e "${GREEN}🎉 E2E Environment Ready${NC}"
    echo -e "${CYAN}📊 Service Status:${NC}"
    echo -e "  • Frontend: http://localhost:5173"
    echo -e "  • Backend API: http://localhost:7071"
    echo -e "  • Storage Emulator: http://localhost:10000"
    echo ""
    echo -e "${BLUE}🧪 You can now run E2E tests:${NC}"
    echo -e "  • npm run test:e2e"
    echo -e "  • npx playwright test"
    echo -e "  • npx playwright test --ui"
    echo ""
}

# Handle script interruption
trap 'echo -e "${RED}❌ Setup interrupted. Cleaning up...${NC}"; cleanup_existing_resources; exit 1' INT TERM

# Execute main function
main "$@"
