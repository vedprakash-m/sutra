#!/bin/bash

# E2E Logs Script
# Provides comprehensive log viewing for E2E environment debugging
# Helps diagnose issues during E2E test runs

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
LOG_LINES=${1:-100}
SERVICE_NAME=${2:-"all"}

echo -e "${BLUE}📋 E2E Environment Logs${NC}"
echo -e "${CYAN}Project: Sutra Multi-LLM Prompt Studio${NC}"
echo -e "${CYAN}Service: $SERVICE_NAME | Lines: $LOG_LINES${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to display service logs
show_service_logs() {
    local service="$1"
    local lines="$2"

    echo -e "${BLUE}📊 $service Service Logs (last $lines lines):${NC}"
    echo -e "${CYAN}============================================${NC}"

    if docker compose logs --tail="$lines" "$service" 2>/dev/null; then
        echo ""
    else
        echo -e "${YELLOW}⚠️  Service '$service' not found or not running${NC}"
        echo ""
    fi
}

# Function to show all service logs
show_all_logs() {
    local lines="$1"

    echo -e "${BLUE}📊 All E2E Services Logs (last $lines lines each):${NC}"
    echo -e "${CYAN}================================================${NC}"

    # Try different compose files to find running services
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    local found_services=false

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            echo -e "${YELLOW}Checking services in $compose_file...${NC}"
            if docker compose -f "$compose_file" ps --services 2>/dev/null | grep -q .; then
                found_services=true
                docker compose -f "$compose_file" logs --tail="$lines"
                echo ""
                break
            fi
        fi
    done

    if [ "$found_services" = false ]; then
        echo -e "${YELLOW}⚠️  No running E2E services found${NC}"
        echo -e "${BLUE}💡 To start E2E services, run: npm run e2e:setup${NC}"
        echo ""
    fi
}

# Function to show service status
show_service_status() {
    echo -e "${BLUE}🔍 Service Status:${NC}"
    echo -e "${CYAN}=================${NC}"

    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            echo -e "${YELLOW}Services in $compose_file:${NC}"
            if docker compose -f "$compose_file" ps 2>/dev/null; then
                echo ""
            else
                echo -e "${YELLOW}  No services running${NC}"
                echo ""
            fi
        fi
    done
}

# Function to show real-time logs
show_realtime_logs() {
    local service="$1"

    echo -e "${BLUE}📊 Real-time logs for $service (press Ctrl+C to stop):${NC}"
    echo -e "${CYAN}================================================${NC}"

    if [ "$service" = "all" ]; then
        docker compose logs -f
    else
        docker compose logs -f "$service"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}📋 E2E Logs Script Help${NC}"
    echo ""
    echo "Usage: $0 [lines] [service] [options]"
    echo ""
    echo "Arguments:"
    echo "  lines    Number of log lines to show (default: 100)"
    echo "  service  Service name to show logs for (default: all)"
    echo ""
    echo "Services:"
    echo "  all                Show logs for all services"
    echo "  frontend          Frontend service logs"
    echo "  functions-api     Backend API service logs"
    echo "  cosmos-emulator   Cosmos DB emulator logs"
    echo "  azurite          Storage emulator logs"
    echo ""
    echo "Options:"
    echo "  --follow, -f     Follow log output in real-time"
    echo "  --status, -s     Show service status"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Show last 100 lines for all services"
    echo "  $0 50                 # Show last 50 lines for all services"
    echo "  $0 200 frontend       # Show last 200 lines for frontend service"
    echo "  $0 --follow           # Follow logs in real-time"
    echo "  $0 --status           # Show service status"
    echo ""
}

# Parse command line arguments
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --status|-s)
        show_service_status
        exit 0
        ;;
    --follow|-f)
        show_realtime_logs "${2:-all}"
        exit 0
        ;;
    *)
        # Default behavior based on arguments
        if [ "$SERVICE_NAME" = "all" ]; then
            show_all_logs "$LOG_LINES"
        else
            show_service_logs "$SERVICE_NAME" "$LOG_LINES"
        fi

        # Always show service status at the end
        show_service_status
        ;;
esac
