#!/bin/bash

# Pre-Commit Docker Configuration Validation
# Ensures Docker files and configurations are consistent before commits
# Prevents CI/CD failures due to missing or misconfigured Docker files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Pre-Commit Docker Configuration Validation${NC}"
echo "=============================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VALIDATION_ERRORS=0

# Function to log validation errors
log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((VALIDATION_ERRORS++))
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Validate Docker file existence
validate_docker_files() {
    echo -e "${BLUE}📋 Validating Docker file existence...${NC}"

    # Check frontend Dockerfile
    if [ ! -f "Dockerfile" ]; then
        log_error "Frontend Dockerfile missing"
    else
        log_success "Frontend Dockerfile exists"
    fi

    if [ ! -f "Dockerfile.e2e" ]; then
        log_error "E2E Dockerfile missing - CI/CD will fail"
    else
        log_success "E2E Dockerfile exists"
    fi

    # Check backend Dockerfile.dev (required by compose files)
    if [ ! -f "api/Dockerfile.dev" ]; then
        log_error "api/Dockerfile.dev missing - required by Docker Compose files"
        log_error "This causes 'open Dockerfile.dev: no such file or directory' in CI/CD"
    else
        log_success "api/Dockerfile.dev exists"
    fi

    # Check standard backend Dockerfile
    if [ ! -f "api/Dockerfile" ]; then
        log_error "api/Dockerfile missing"
    else
        log_success "api/Dockerfile exists"
    fi
}

# Validate Docker Compose file references
validate_docker_compose_references() {
    echo -e "${BLUE}🔗 Validating Docker Compose file references...${NC}"

    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [ ! -f "$compose_file" ]; then
            log_error "Docker Compose file missing: $compose_file"
            continue
        fi

        # Check if it references Dockerfile.dev
        if grep -q "dockerfile: Dockerfile.dev" "$compose_file"; then
            # Verify the referenced file exists
            local dockerfile_path="api/Dockerfile.dev"
            if [ ! -f "$dockerfile_path" ]; then
                log_error "$compose_file references $dockerfile_path but file doesn't exist"
            else
                log_success "$compose_file references existing $dockerfile_path"
            fi
        fi

        # Check if it references other Dockerfiles
        if grep -q "dockerfile: Dockerfile.e2e" "$compose_file"; then
            if [ ! -f "Dockerfile.e2e" ]; then
                log_error "$compose_file references Dockerfile.e2e but file doesn't exist"
            else
                log_success "$compose_file references existing Dockerfile.e2e"
            fi
        fi
    done
}

# Validate Dockerfile content
validate_dockerfile_content() {
    echo -e "${BLUE}📝 Validating Dockerfile content...${NC}"

    # Validate api/Dockerfile.dev
    if [ -f "api/Dockerfile.dev" ]; then
        # Check for required Azure Functions environment variables
        if ! grep -q "AzureWebJobsScriptRoot" api/Dockerfile.dev; then
            log_error "api/Dockerfile.dev missing AzureWebJobsScriptRoot environment variable"
        else
            log_success "api/Dockerfile.dev has required environment variables"
        fi

        # Check for proper file copying to Azure Functions location
        if ! grep -q "COPY.*/home/site/wwwroot" api/Dockerfile.dev; then
            log_error "api/Dockerfile.dev not copying files to /home/site/wwwroot"
        else
            log_success "api/Dockerfile.dev copies files to correct location"
        fi

        # Check for curl installation (needed for health checks)
        if grep -q "curl" api/Dockerfile.dev; then
            log_success "api/Dockerfile.dev includes curl for health checks"
        else
            log_warning "api/Dockerfile.dev missing curl - health checks may fail"
        fi
    fi
}

# Validate requirements file references
validate_requirements_references() {
    echo -e "${BLUE}📦 Validating requirements file references...${NC}"

    if [ -f "api/Dockerfile.dev" ]; then
        # Check which requirements file is used
        if grep -q "requirements-minimal.txt" api/Dockerfile.dev; then
            if [ ! -f "api/requirements-minimal.txt" ]; then
                log_error "api/Dockerfile.dev references requirements-minimal.txt but file doesn't exist"
            else
                log_success "api/Dockerfile.dev uses existing requirements-minimal.txt"
            fi
        elif grep -q "requirements.txt" api/Dockerfile.dev; then
            if [ ! -f "api/requirements.txt" ]; then
                log_error "api/Dockerfile.dev references requirements.txt but file doesn't exist"
            else
                log_success "api/Dockerfile.dev uses existing requirements.txt"
            fi
        else
            log_error "api/Dockerfile.dev doesn't specify requirements file"
        fi
    fi
}

# Validate health check configuration
validate_health_check_config() {
    echo -e "${BLUE}🏥 Validating health check configuration...${NC}"

    # Check if health endpoint exists
    if [ ! -f "api/health/__init__.py" ]; then
        log_error "Health endpoint api/health/__init__.py missing"
    else
        log_success "Health endpoint exists"
    fi

    if [ ! -f "api/health/function.json" ]; then
        log_error "Health function configuration api/health/function.json missing"
    else
        log_success "Health function configuration exists"
    fi

    # Check Docker Compose health check configurations
    for compose_file in docker-compose*.yml; do
        if [ -f "$compose_file" ] && grep -q "healthcheck:" "$compose_file"; then
            if grep -A 5 "healthcheck:" "$compose_file" | grep -q "curl"; then
                # Verify curl is available in Dockerfile
                if [ -f "api/Dockerfile.dev" ] && ! grep -q "curl" api/Dockerfile.dev; then
                    log_error "$compose_file uses curl health check but api/Dockerfile.dev doesn't install curl"
                else
                    log_success "$compose_file health check configuration valid"
                fi
            fi
        fi
    done
}

# Test Docker Compose configuration validity
validate_docker_compose_syntax() {
    echo -e "${BLUE}🧪 Testing Docker Compose syntax...${NC}"

    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            # Test with modern docker compose first
            if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
                if docker compose -f "$compose_file" config >/dev/null 2>&1; then
                    log_success "$compose_file syntax valid"
                else
                    log_error "$compose_file syntax invalid"
                fi
            elif command -v docker-compose &> /dev/null; then
                if docker-compose -f "$compose_file" config >/dev/null 2>&1; then
                    log_success "$compose_file syntax valid (legacy)"
                else
                    log_error "$compose_file syntax invalid"
                fi
            else
                log_warning "Docker not available - cannot validate $compose_file syntax"
            fi
        fi
    done
}

# Main validation execution
main() {
    validate_docker_files
    validate_docker_compose_references
    validate_dockerfile_content
    validate_requirements_references
    validate_health_check_config
    validate_docker_compose_syntax

    echo ""
    echo "=============================================="
    if [ $VALIDATION_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ All Docker configuration validations passed${NC}"
        exit 0
    else
        echo -e "${RED}❌ Found $VALIDATION_ERRORS Docker configuration issues${NC}"
        echo -e "${YELLOW}These issues will cause CI/CD failures${NC}"
        exit 1
    fi
}

main "$@"
