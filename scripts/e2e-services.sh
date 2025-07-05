#!/bin/bash

# E2E Services Script
# Provides comprehensive service management for E2E environment
# Allows granular control over individual services

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
ACTION=${1:-"status"}
SERVICE_NAME=${2:-"all"}

echo -e "${BLUE}🔧 E2E Services Management${NC}"
echo -e "${CYAN}Project: Sutra Multi-LLM Prompt Studio${NC}"
echo -e "${CYAN}Action: $ACTION | Service: $SERVICE_NAME${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to determine active compose file
get_active_compose_file() {
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ] && docker compose -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
            echo "$compose_file"
            return 0
        fi
    done

    # Default to e2e-no-cosmos if none are active
    echo "docker-compose.e2e-no-cosmos.yml"
}

# Function to show service status
show_service_status() {
    echo -e "${BLUE}🔍 Service Status:${NC}"
    echo -e "${CYAN}=================${NC}"

    local compose_file=$(get_active_compose_file)

    if docker compose -f "$compose_file" ps 2>/dev/null; then
        echo ""
        echo -e "${BLUE}📊 Health Check Status:${NC}"
        echo -e "${CYAN}======================${NC}"

        # Check individual service health
        check_service_health "Frontend" "http://localhost:5173"
        check_service_health "Backend API" "http://localhost:7071/api/health"
        check_service_health "Storage Emulator" "http://localhost:10000"

        if docker compose -f "$compose_file" ps | grep -q cosmos-emulator; then
            check_service_health "Cosmos DB Emulator" "https://localhost:8081/_explorer/index.html"
        fi
    else
        echo -e "${YELLOW}⚠️  No services are currently running${NC}"
        echo -e "${BLUE}💡 To start services, run: npm run e2e:setup${NC}"
    fi
    echo ""
}

# Function to check service health
check_service_health() {
    local service_name="$1"
    local health_url="$2"

    if curl -f "$health_url" --max-time 5 --silent > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $service_name: Healthy${NC}"
    else
        echo -e "  ${RED}❌ $service_name: Unhealthy${NC}"
    fi
}

# Function to start services
start_services() {
    local service="$1"
    local compose_file=$(get_active_compose_file)

    echo -e "${BLUE}🚀 Starting services...${NC}"

    if [ "$service" = "all" ]; then
        docker compose -f "$compose_file" up -d
        echo -e "${GREEN}✅ All services started${NC}"
    else
        docker compose -f "$compose_file" up -d "$service"
        echo -e "${GREEN}✅ Service '$service' started${NC}"
    fi

    echo ""
    show_service_status
}

# Function to stop services
stop_services() {
    local service="$1"
    local compose_file=$(get_active_compose_file)

    echo -e "${BLUE}🛑 Stopping services...${NC}"

    if [ "$service" = "all" ]; then
        docker compose -f "$compose_file" down
        echo -e "${GREEN}✅ All services stopped${NC}"
    else
        docker compose -f "$compose_file" stop "$service"
        echo -e "${GREEN}✅ Service '$service' stopped${NC}"
    fi

    echo ""
}

# Function to restart services
restart_services() {
    local service="$1"
    local compose_file=$(get_active_compose_file)

    echo -e "${BLUE}🔄 Restarting services...${NC}"

    if [ "$service" = "all" ]; then
        docker compose -f "$compose_file" restart
        echo -e "${GREEN}✅ All services restarted${NC}"
    else
        docker compose -f "$compose_file" restart "$service"
        echo -e "${GREEN}✅ Service '$service' restarted${NC}"
    fi

    echo ""
    show_service_status
}

# Function to show service logs
show_service_logs() {
    local service="$1"
    local compose_file=$(get_active_compose_file)

    echo -e "${BLUE}📋 Service Logs:${NC}"
    echo -e "${CYAN}================${NC}"

    if [ "$service" = "all" ]; then
        docker compose -f "$compose_file" logs --tail=50
    else
        docker compose -f "$compose_file" logs --tail=50 "$service"
    fi

    echo ""
}

# Function to execute command in service
exec_in_service() {
    local service="$1"
    local command="$2"
    local compose_file=$(get_active_compose_file)

    echo -e "${BLUE}🔧 Executing command in $service:${NC}"
    echo -e "${CYAN}Command: $command${NC}"
    echo ""

    docker compose -f "$compose_file" exec "$service" $command
}

# Function to show available services
show_available_services() {
    local compose_file=$(get_active_compose_file)

    echo -e "${BLUE}📋 Available Services:${NC}"
    echo -e "${CYAN}=====================${NC}"

    if [ -f "$compose_file" ]; then
        docker compose -f "$compose_file" config --services
    else
        echo -e "${YELLOW}⚠️  No compose file found${NC}"
    fi

    echo ""
}

# Function to show resource usage
show_resource_usage() {
    echo -e "${BLUE}📊 Resource Usage:${NC}"
    echo -e "${CYAN}==================${NC}"

    # Show Docker stats for running containers
    if docker ps --filter "name=sutra-*" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q .; then
        echo -e "${YELLOW}Running Containers:${NC}"
        docker ps --filter "name=sutra-*" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""

        echo -e "${YELLOW}Resource Usage:${NC}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker ps --filter "name=sutra-*" --format "{{.Names}}")
    else
        echo -e "${YELLOW}⚠️  No running containers found${NC}"
    fi

    echo ""
}

# Function to show help
show_help() {
    echo -e "${BLUE}📋 E2E Services Script Help${NC}"
    echo ""
    echo "Usage: $0 [action] [service]"
    echo ""
    echo "Actions:"
    echo "  status     Show service status (default)"
    echo "  start      Start services"
    echo "  stop       Stop services"
    echo "  restart    Restart services"
    echo "  logs       Show service logs"
    echo "  exec       Execute command in service"
    echo "  list       Show available services"
    echo "  resources  Show resource usage"
    echo "  help       Show this help message"
    echo ""
    echo "Services:"
    echo "  all                All services (default)"
    echo "  frontend          Frontend service"
    echo "  functions-api     Backend API service"
    echo "  cosmos-emulator   Cosmos DB emulator"
    echo "  azurite          Storage emulator"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Show status of all services"
    echo "  $0 start frontend            # Start frontend service"
    echo "  $0 stop functions-api        # Stop backend API service"
    echo "  $0 restart all               # Restart all services"
    echo "  $0 logs frontend             # Show frontend logs"
    echo "  $0 exec functions-api bash   # Execute bash in backend service"
    echo "  $0 list                      # Show available services"
    echo "  $0 resources                 # Show resource usage"
    echo ""
}

# Main execution logic
case "$ACTION" in
    status)
        show_service_status
        ;;
    start)
        start_services "$SERVICE_NAME"
        ;;
    stop)
        stop_services "$SERVICE_NAME"
        ;;
    restart)
        restart_services "$SERVICE_NAME"
        ;;
    logs)
        show_service_logs "$SERVICE_NAME"
        ;;
    exec)
        if [ -z "$3" ]; then
            echo -e "${RED}❌ Command required for exec action${NC}"
            echo "Usage: $0 exec [service] [command]"
            exit 1
        fi
        exec_in_service "$SERVICE_NAME" "$3"
        ;;
    list)
        show_available_services
        ;;
    resources)
        show_resource_usage
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown action: $ACTION${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
