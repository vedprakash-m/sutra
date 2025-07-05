#!/bin/bash

# Enhanced E2E Cleanup Script
# Provides comprehensive E2E environment cleanup with proper resource management
# Ensures clean state for subsequent test runs

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

echo -e "${BLUE}🧹 Enhanced E2E Environment Cleanup${NC}"
echo -e "${CYAN}Project: Sutra Multi-LLM Prompt Studio${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to log with timestamp
log_with_time() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Function to cleanup Docker resources
cleanup_docker_resources() {
    echo -e "${BLUE}🐳 Cleaning up Docker resources...${NC}"

    # Stop and remove containers from all possible compose files
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
        "docker-compose.test.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            log_with_time "Stopping services from $compose_file..."
            docker compose -f "$compose_file" down --remove-orphans --volumes --timeout 30 > /dev/null 2>&1 || true
        fi
    done

    # Clean up any leftover sutra-related containers
    log_with_time "Cleaning up sutra-related containers..."
    docker container ls -a --filter "name=sutra-*" --format "{{.Names}}" | xargs -I {} docker container rm -f {} > /dev/null 2>&1 || true

    # Clean up volumes
    log_with_time "Cleaning up volumes..."
    docker volume ls --filter "name=sutra-*" --format "{{.Name}}" | xargs -I {} docker volume rm {} > /dev/null 2>&1 || true

    # Clean up networks
    log_with_time "Cleaning up networks..."
    docker network ls --filter "name=sutra-*" --format "{{.Name}}" | xargs -I {} docker network rm {} > /dev/null 2>&1 || true

    # General cleanup
    log_with_time "Running general Docker cleanup..."
    docker container prune -f > /dev/null 2>&1 || true
    docker network prune -f > /dev/null 2>&1 || true
    docker volume prune -f > /dev/null 2>&1 || true

    echo -e "${GREEN}✅ Docker resources cleaned up${NC}"
}

# Function to cleanup test artifacts
cleanup_test_artifacts() {
    echo -e "${BLUE}🗑️  Cleaning up test artifacts...${NC}"

    # Remove Playwright test results
    if [ -d "test-results" ]; then
        rm -rf test-results
        log_with_time "Removed test-results directory"
    fi

    # Remove Playwright reports
    if [ -d "playwright-report" ]; then
        rm -rf playwright-report
        log_with_time "Removed playwright-report directory"
    fi

    # Remove coverage reports
    if [ -d "coverage" ]; then
        rm -rf coverage
        log_with_time "Removed coverage directory"
    fi

    # Remove test setup markers
    if [ -f "/tmp/sutra-e2e-setup-complete" ]; then
        rm -f /tmp/sutra-e2e-setup-complete
        log_with_time "Removed test setup marker"
    fi

    # Remove temporary log files
    rm -f /tmp/test_output /tmp/e2e_*.log /tmp/eslint.log /tmp/typecheck.log /tmp/prettier.log

    echo -e "${GREEN}✅ Test artifacts cleaned up${NC}"
}

# Function to cleanup background processes
cleanup_background_processes() {
    echo -e "${BLUE}🔄 Cleaning up background processes...${NC}"

    # Kill any background Node.js processes (dev servers, etc.)
    local node_processes=$(pgrep -f "node.*vite\|node.*dev\|node.*serve" 2>/dev/null || true)
    if [ -n "$node_processes" ]; then
        echo "$node_processes" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$node_processes" | xargs kill -KILL 2>/dev/null || true
        log_with_time "Killed Node.js dev processes"
    fi

    # Kill any background Python processes (Azure Functions, etc.)
    local python_processes=$(pgrep -f "python.*func\|python.*azure" 2>/dev/null || true)
    if [ -n "$python_processes" ]; then
        echo "$python_processes" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$python_processes" | xargs kill -KILL 2>/dev/null || true
        log_with_time "Killed Python func processes"
    fi

    echo -e "${GREEN}✅ Background processes cleaned up${NC}"
}

# Function to free up ports
free_up_ports() {
    echo -e "${BLUE}🔌 Freeing up ports...${NC}"

    local ports=(3000 5173 7071 8081 10000 10001 10002 10251 10252 10253 10254)

    for port in "${ports[@]}"; do
        local pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            kill -TERM "$pid" 2>/dev/null || true
            sleep 1
            kill -KILL "$pid" 2>/dev/null || true
            log_with_time "Freed port $port (PID: $pid)"
        fi
    done

    echo -e "${GREEN}✅ Ports freed up${NC}"
}

# Function to validate cleanup
validate_cleanup() {
    echo -e "${BLUE}🔍 Validating cleanup...${NC}"

    # Check if any sutra containers are still running
    local running_containers=$(docker container ls --filter "name=sutra-*" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$running_containers" ]; then
        echo -e "${YELLOW}⚠️  Some containers are still running: $running_containers${NC}"
        return 1
    fi

    # Check if ports are free
    local busy_ports=()
    local ports=(3000 5173 7071 8081 10000 10001 10002)

    for port in "${ports[@]}"; do
        if lsof -ti:$port > /dev/null 2>&1; then
            busy_ports+=($port)
        fi
    done

    if [ ${#busy_ports[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Some ports are still in use: ${busy_ports[*]}${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Cleanup validation passed${NC}"
    return 0
}

# Function to display cleanup summary
display_cleanup_summary() {
    echo ""
    echo -e "${GREEN}🎉 E2E Environment Cleanup Completed${NC}"
    echo -e "${CYAN}📊 Cleanup Summary:${NC}"
    echo -e "  • Docker containers: Stopped and removed"
    echo -e "  • Docker volumes: Cleaned up"
    echo -e "  • Docker networks: Cleaned up"
    echo -e "  • Test artifacts: Removed"
    echo -e "  • Background processes: Terminated"
    echo -e "  • Ports: Freed up"
    echo ""
    echo -e "${BLUE}💡 The environment is now clean and ready for the next test run${NC}"
    echo ""
}

# Main execution flow
main() {
    log_with_time "Starting E2E environment cleanup..."

    # Step 1: Cleanup Docker resources
    cleanup_docker_resources

    # Step 2: Cleanup test artifacts
    cleanup_test_artifacts

    # Step 3: Cleanup background processes
    cleanup_background_processes

    # Step 4: Free up ports
    free_up_ports

    # Step 5: Validate cleanup
    if validate_cleanup; then
        log_with_time "Cleanup validation successful"
    else
        log_with_time "Cleanup validation failed - some resources may still be in use"
        echo -e "${YELLOW}⚠️  Note: Some resources may still be in use by other processes${NC}"
    fi

    # Step 6: Display summary
    display_cleanup_summary

    log_with_time "E2E environment cleanup completed!"
}

# Handle script interruption
trap 'echo -e "${RED}❌ Cleanup interrupted${NC}"; exit 1' INT TERM

# Execute main function
main "$@"
