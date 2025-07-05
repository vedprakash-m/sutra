#!/bin/bash

# E2E Validation Script
# Provides comprehensive validation of E2E environment setup
# Ensures all components are properly configured before running tests

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
VALIDATION_MODE=${1:-"full"}
TIMEOUT_SECONDS=60

echo -e "${BLUE}🔍 E2E Environment Validation${NC}"
echo -e "${CYAN}Project: Sutra Multi-LLM Prompt Studio${NC}"
echo -e "${CYAN}Mode: $VALIDATION_MODE${NC}"
echo ""

cd "$PROJECT_ROOT"

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
ISSUES_FOUND=()

# Function to run validation check
run_validation() {
    local check_name="$1"
    local check_command="$2"
    local is_critical="${3:-true}"

    ((TOTAL_CHECKS++))

    echo -e "${BLUE}🔍 Validating: $check_name${NC}"

    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $check_name: PASSED${NC}"
        ((PASSED_CHECKS++))
        return 0
    else
        echo -e "${RED}❌ $check_name: FAILED${NC}"
        ((FAILED_CHECKS++))

        if [ "$is_critical" = "true" ]; then
            ISSUES_FOUND+=("CRITICAL: $check_name")
        else
            ISSUES_FOUND+=("WARNING: $check_name")
        fi

        return 1
    fi
}

# Function to validate prerequisites
validate_prerequisites() {
    echo -e "${BLUE}📋 Validating Prerequisites${NC}"
    echo -e "${CYAN}============================${NC}"

    run_validation "Docker daemon" "docker info"
    run_validation "Docker Compose" "docker compose version"
    run_validation "Node.js" "node --version"
    run_validation "npm" "npm --version"
    run_validation "Python" "python3 --version"
    run_validation "curl" "curl --version"

    echo ""
}

# Function to validate project structure
validate_project_structure() {
    echo -e "${BLUE}📁 Validating Project Structure${NC}"
    echo -e "${CYAN}================================${NC}"

    run_validation "package.json exists" "test -f package.json"
    run_validation "Docker Compose files exist" "test -f docker-compose.yml && test -f docker-compose.e2e-no-cosmos.yml"
    run_validation "Playwright config exists" "test -f playwright.config.ts"
    run_validation "API directory exists" "test -d api"
    run_validation "E2E tests directory exists" "test -d tests/e2e"
    run_validation "Scripts directory exists" "test -d scripts"

    echo ""
}

# Function to validate dependencies
validate_dependencies() {
    echo -e "${BLUE}📦 Validating Dependencies${NC}"
    echo -e "${CYAN}===========================${NC}"

    run_validation "Node.js dependencies" "npm ls @playwright/test"
    run_validation "Playwright browsers" "npx playwright --version"

    # Check Python dependencies
    cd api
    run_validation "Python Azure Functions" "python3 -c 'import azure.functions'"
    run_validation "Python requirements" "pip show azure-functions"
    cd ..

    echo ""
}

# Function to validate Docker environment
validate_docker_environment() {
    echo -e "${BLUE}🐳 Validating Docker Environment${NC}"
    echo -e "${CYAN}===============================${NC}"

    # Check if services are running
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    local services_running=false

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ] && docker compose -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
            services_running=true
            echo -e "${GREEN}✅ Services running with $compose_file${NC}"
            break
        fi
    done

    if [ "$services_running" = false ]; then
        echo -e "${YELLOW}⚠️  No E2E services currently running${NC}"
        echo -e "${BLUE}💡 Run 'npm run e2e:setup' to start services${NC}"
        ISSUES_FOUND+=("WARNING: No E2E services running")
    fi

    echo ""
}

# Function to validate service connectivity
validate_service_connectivity() {
    echo -e "${BLUE}🔗 Validating Service Connectivity${NC}"
    echo -e "${CYAN}==================================${NC}"

    # Check if services are accessible
    local services=(
        "Frontend:http://localhost:5173"
        "Backend API:http://localhost:7071/api/health"
        "Storage Emulator:http://localhost:10000"
    )

    local any_service_accessible=false

    for service_info in "${services[@]}"; do
        local service_name=$(echo "$service_info" | cut -d':' -f1)
        local service_url=$(echo "$service_info" | cut -d':' -f2-)

        if curl -f "$service_url" --max-time 5 --silent > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name: Accessible${NC}"
            any_service_accessible=true
        else
            echo -e "${RED}❌ $service_name: Not accessible${NC}"
            ISSUES_FOUND+=("WARNING: $service_name not accessible")
        fi
    done

    if [ "$any_service_accessible" = false ]; then
        ISSUES_FOUND+=("CRITICAL: No services accessible")
    fi

    echo ""
}

# Function to validate E2E test configuration
validate_e2e_configuration() {
    echo -e "${BLUE}🧪 Validating E2E Test Configuration${NC}"
    echo -e "${CYAN}===================================${NC}"

    # Check Playwright configuration
    run_validation "Playwright config syntax" "npx playwright --help"

    # Check if test files exist
    local test_files=(
        "tests/e2e/auth.spec.ts"
        "tests/e2e/basic-navigation.spec.ts"
        "tests/e2e/collection-management.spec.ts"
        "tests/e2e/prompt-builder.spec.ts"
    )

    local test_files_exist=0
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            ((test_files_exist++))
        fi
    done

    if [ $test_files_exist -gt 0 ]; then
        echo -e "${GREEN}✅ E2E test files: $test_files_exist found${NC}"
    else
        echo -e "${RED}❌ E2E test files: None found${NC}"
        ISSUES_FOUND+=("WARNING: No E2E test files found")
    fi

    # Check global setup/teardown
    run_validation "Global setup exists" "test -f tests/e2e/global-setup.ts"
    run_validation "Global teardown exists" "test -f tests/e2e/global-teardown.ts"

    echo ""
}

# Function to validate environment variables
validate_environment_variables() {
    echo -e "${BLUE}🌍 Validating Environment Variables${NC}"
    echo -e "${CYAN}===================================${NC}"

    # Check if important environment variables are set
    local env_vars=(
        "NODE_ENV"
        "VITE_API_BASE_URL"
        "FUNCTIONS_WORKER_RUNTIME"
    )

    for env_var in "${env_vars[@]}"; do
        if [ -n "${!env_var}" ]; then
            echo -e "${GREEN}✅ $env_var: Set${NC}"
        else
            echo -e "${YELLOW}⚠️  $env_var: Not set${NC}"
            ISSUES_FOUND+=("INFO: $env_var not set")
        fi
    done

    echo ""
}

# Function to validate port availability
validate_port_availability() {
    echo -e "${BLUE}🔌 Validating Port Availability${NC}"
    echo -e "${CYAN}===============================${NC}"

    local ports=(3000 5173 7071 8081 10000 10001 10002)
    local ports_in_use=()

    for port in "${ports[@]}"; do
        if lsof -ti:$port > /dev/null 2>&1; then
            ports_in_use+=($port)
        fi
    done

    if [ ${#ports_in_use[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Ports in use: ${ports_in_use[*]} (services running)${NC}"
    else
        echo -e "${YELLOW}⚠️  No ports in use (services not running)${NC}"
        ISSUES_FOUND+=("INFO: No services currently running")
    fi

    echo ""
}

# Function to run quick smoke tests
run_smoke_tests() {
    echo -e "${BLUE}💨 Running Smoke Tests${NC}"
    echo -e "${CYAN}======================${NC}"

    # Test if we can run a simple Playwright command
    if npx playwright --version > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Playwright command: Working${NC}"
    else
        echo -e "${RED}❌ Playwright command: Failed${NC}"
        ISSUES_FOUND+=("CRITICAL: Playwright not working")
    fi

    # Test if we can list tests
    if npx playwright test --list > /dev/null 2>&1; then
        local test_count=$(npx playwright test --list | wc -l)
        echo -e "${GREEN}✅ E2E tests discoverable: $test_count tests found${NC}"
    else
        echo -e "${RED}❌ E2E tests not discoverable${NC}"
        ISSUES_FOUND+=("WARNING: E2E tests not discoverable")
    fi

    echo ""
}

# Function to show validation summary
show_validation_summary() {
    echo -e "${BLUE}📊 Validation Summary${NC}"
    echo -e "${CYAN}===================${NC}"

    echo -e "Total checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"

    if [ ${#ISSUES_FOUND[@]} -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Issues Found:${NC}"
        for issue in "${ISSUES_FOUND[@]}"; do
            echo -e "  • $issue"
        done
    fi

    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 All validations passed! E2E environment is ready.${NC}"
        return 0
    else
        echo -e "${RED}❌ Some validations failed. Please review and fix the issues above.${NC}"
        return 1
    fi
}

# Main execution flow
main() {
    echo "Starting E2E environment validation..."
    echo ""

    # Run different validation suites based on mode
    case "$VALIDATION_MODE" in
        "quick")
            validate_prerequisites
            validate_project_structure
            ;;
        "full")
            validate_prerequisites
            validate_project_structure
            validate_dependencies
            validate_docker_environment
            validate_service_connectivity
            validate_e2e_configuration
            validate_environment_variables
            validate_port_availability
            run_smoke_tests
            ;;
        "connectivity")
            validate_service_connectivity
            validate_port_availability
            ;;
        "config")
            validate_e2e_configuration
            validate_environment_variables
            ;;
        *)
            echo -e "${RED}❌ Unknown validation mode: $VALIDATION_MODE${NC}"
            echo "Available modes: quick, full, connectivity, config"
            exit 1
            ;;
    esac

    show_validation_summary
}

# Execute main function
main "$@"
