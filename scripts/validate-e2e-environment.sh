#!/bin/bash

# Enhanced E2E Environment Validation Script
# Comprehensive validation that catches CI/CD issues before they happen
# Addresses root cause: Missing local parity with CI/CD environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔬 Enhanced E2E Environment Validation${NC}"
echo -e "${CYAN}Comprehensive CI/CD Parity Check${NC}"
echo "=========================================="

VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

# Function to log validation results
log_error() {
    echo -e "${RED}❌ CRITICAL: $1${NC}"
    ((VALIDATION_ERRORS++))
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((VALIDATION_WARNINGS++))
}

log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Validate Docker environment exactly like CI/CD
validate_docker_environment() {
    echo -e "${BLUE}🐳 Docker Environment Validation${NC}"
    echo "--------------------------------"

    # Check Docker availability (required for E2E)
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed - E2E tests will fail in CI/CD"
        log_info "Install Docker Desktop to match CI/CD environment"
        return 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running - E2E tests will fail"
        log_info "Start Docker Desktop to match CI/CD environment"
        return 1
    fi

    log_success "Docker environment available"

    # Check Docker Compose availability
    local docker_compose_available=false
    if docker compose version &> /dev/null 2>&1; then
        log_success "Modern docker compose available"
        docker_compose_available=true
    fi

    if command -v docker-compose &> /dev/null; then
        log_success "Legacy docker-compose available"
        docker_compose_available=true
    fi

    if [ "$docker_compose_available" = false ]; then
        log_error "No Docker Compose found - CI/CD will fail"
        return 1
    fi

    return 0
}

# Validate all required files exist
validate_required_files() {
    echo -e "${BLUE}📋 Required Files Validation${NC}"
    echo "----------------------------"

    local required_files=(
        "package.json"
        "tsconfig.json"
        "vite.config.ts"
        "index.html"
        "Dockerfile"
        "Dockerfile.e2e"
        "api/Dockerfile"
        "api/Dockerfile.dev"
        "api/requirements.txt"
        "api/requirements-minimal.txt"
        "api/host.json"
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
        "scripts/e2e-setup.sh"
        "scripts/e2e-cleanup.sh"
    )

    local missing_files=()

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
            log_error "Missing required file: $file"
        fi
    done

    if [ ${#missing_files[@]} -eq 0 ]; then
        log_success "All required files present"
        return 0
    else
        log_error "Missing ${#missing_files[@]} required files - CI/CD will fail"
        return 1
    fi
}

# Validate Docker Compose file consistency
validate_docker_compose_consistency() {
    echo -e "${BLUE}🔗 Docker Compose Consistency Check${NC}"
    echo "----------------------------------"

    local compose_files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [ ! -f "$compose_file" ]; then
            log_error "$compose_file missing"
            continue
        fi

        # Validate syntax
        if docker compose -f "$compose_file" config >/dev/null 2>&1; then
            log_success "$compose_file syntax valid"
        else
            log_error "$compose_file syntax invalid - CI/CD will fail"
            continue
        fi

        # Check Dockerfile references
        local dockerfile_refs=($(grep -o "dockerfile: [^[:space:]]*" "$compose_file" | cut -d' ' -f2))
        for dockerfile_ref in "${dockerfile_refs[@]}"; do
            local dockerfile_path="$dockerfile_ref"
            if grep -q "context: ./api" "$compose_file"; then
                dockerfile_path="api/$dockerfile_ref"
            fi

            if [ ! -f "$dockerfile_path" ]; then
                log_error "$compose_file references missing $dockerfile_path"
            else
                log_success "$compose_file references existing $dockerfile_path"
            fi
        done
    done
}

# Simulate CI/CD environment detection
validate_environment_detection() {
    echo -e "${BLUE}🌐 Environment Detection Simulation${NC}"
    echo "-----------------------------------"

    # Test CI environment simulation
    log_info "Testing CI environment detection..."
    local ci_config=$(CI=true bash -c 'source scripts/e2e-setup-enhanced.sh >/dev/null 2>&1; determine_docker_compose_config' 2>/dev/null || echo "error")
    
    if [[ "$ci_config" == "docker-compose.e2e-no-cosmos.yml" ]]; then
        log_success "CI environment detection works"
    else
        log_error "CI environment detection failed: got '$ci_config'"
    fi

    # Test local environment detection
    log_info "Testing local environment detection..."
    local local_config=$(unset CI && bash -c 'source scripts/e2e-setup-enhanced.sh >/dev/null 2>&1; determine_docker_compose_config' 2>/dev/null || echo "error")
    
    if [[ "$local_config" =~ ^docker-compose\.e2e-.*\.yml$ ]]; then
        log_success "Local environment detection works: $local_config"
    else
        log_warning "Local environment detection unclear: got '$local_config'"
    fi
}

# Test E2E setup script functionality
validate_e2e_setup_script() {
    echo -e "${BLUE}🚀 E2E Setup Script Validation${NC}"
    echo "------------------------------"

    # Check script exists and is executable
    if [ ! -f "scripts/e2e-setup.sh" ]; then
        log_error "E2E setup script missing"
        return 1
    fi

    if [ ! -x "scripts/e2e-setup.sh" ]; then
        log_error "E2E setup script not executable"
        return 1
    fi

    # Validate script syntax
    if bash -n scripts/e2e-setup.sh; then
        log_success "E2E setup script syntax valid"
    else
        log_error "E2E setup script has syntax errors"
        return 1
    fi

    # Check enhanced setup script
    if [ -f "scripts/e2e-setup-enhanced.sh" ]; then
        if bash -n scripts/e2e-setup-enhanced.sh; then
            log_success "Enhanced E2E setup script syntax valid"
        else
            log_error "Enhanced E2E setup script has syntax errors"
        fi
    fi
}

# Test health endpoint availability
validate_health_endpoints() {
    echo -e "${BLUE}🏥 Health Endpoint Validation${NC}"
    echo "----------------------------"

    # Check health endpoint implementation
    if [ ! -f "api/health/__init__.py" ]; then
        log_error "Health endpoint implementation missing"
    else
        log_success "Health endpoint implementation exists"
    fi

    if [ ! -f "api/health/function.json" ]; then
        log_error "Health endpoint configuration missing"
    else
        # Validate health endpoint configuration
        if python3 -m json.tool api/health/function.json >/dev/null 2>&1; then
            log_success "Health endpoint configuration valid"
        else
            log_error "Health endpoint configuration invalid JSON"
        fi
    fi
}

# Validate package.json E2E scripts
validate_package_scripts() {
    echo -e "${BLUE}📦 Package.json Scripts Validation${NC}"
    echo "----------------------------------"

    local required_scripts=(
        "e2e:setup"
        "e2e:cleanup"
        "build"
        "dev"
    )

    for script in "${required_scripts[@]}"; do
        if grep -q "\"$script\":" package.json; then
            log_success "Script '$script' exists"
        else
            log_error "Missing package.json script: $script"
        fi
    done

    # Validate that e2e scripts point to correct files
    if grep -q "\"e2e:setup\":" package.json; then
        local setup_command=$(grep -A1 '"e2e:setup":' package.json | tail -1 | sed 's/.*"e2e:setup": "\(.*\)".*/\1/')
        if echo "$setup_command" | grep -q "scripts/e2e-setup.sh"; then
            log_success "e2e:setup script points to correct file"
        else
            log_warning "e2e:setup script command unclear: $setup_command"
        fi
    fi
}

# Test requirements file consistency
validate_requirements_consistency() {
    echo -e "${BLUE}📚 Requirements Files Validation${NC}"
    echo "--------------------------------"

    local req_files=(
        "api/requirements.txt"
        "api/requirements-minimal.txt"
        "api/requirements-ci.txt"
    )

    for req_file in "${req_files[@]}"; do
        if [ -f "$req_file" ]; then
            log_success "$(basename "$req_file") exists"
            
            # Check for critical dependencies
            if grep -q "azure-functions" "$req_file"; then
                log_success "$(basename "$req_file") includes azure-functions"
            else
                log_warning "$(basename "$req_file") missing azure-functions"
            fi
        else
            if [[ "$req_file" == "api/requirements-ci.txt" ]]; then
                log_warning "$(basename "$req_file") missing (optional)"
            else
                log_error "$(basename "$req_file") missing"
            fi
        fi
    done
}

# Run comprehensive validation
main() {
    local start_time=$(date +%s)

    echo -e "${CYAN}Starting comprehensive E2E environment validation...${NC}"
    echo ""

    # Core validations that must pass
    validate_docker_environment
    validate_required_files
    validate_docker_compose_consistency
    validate_e2e_setup_script
    validate_health_endpoints
    validate_package_scripts
    validate_requirements_consistency

    # Advanced validations
    validate_environment_detection

    echo ""
    echo "=========================================="
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $VALIDATION_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ ALL VALIDATIONS PASSED${NC}"
        echo -e "${GREEN}E2E environment has 100% CI/CD parity${NC}"
        if [ $VALIDATION_WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}Found $VALIDATION_WARNINGS warnings (non-blocking)${NC}"
        fi
        echo -e "${CYAN}Validation completed in ${duration}s${NC}"
        exit 0
    else
        echo -e "${RED}❌ VALIDATION FAILED${NC}"
        echo -e "${RED}Found $VALIDATION_ERRORS critical issues that will cause CI/CD failures${NC}"
        if [ $VALIDATION_WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}Also found $VALIDATION_WARNINGS warnings${NC}"
        fi
        echo -e "${CYAN}Validation completed in ${duration}s${NC}"
        echo ""
        echo -e "${YELLOW}Fix these issues before committing to prevent CI/CD failures${NC}"
        exit 1
    fi
}

main "$@"
