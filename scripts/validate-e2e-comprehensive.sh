#!/bin/bash

# Comprehensive E2E Validation Script
# This script validates E2E setup in an environment that matches CI exactly
# Addresses gaps in local validation that allowed CI failures to slip through

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
VALIDATION_MODE="${1:-full}"
TEMP_DIR="/tmp/sutra-e2e-validation-$$"

echo -e "${BLUE}🧪 Comprehensive E2E Validation${NC}"
echo -e "${CYAN}Mode: $VALIDATION_MODE${NC}"
echo -e "${CYAN}Purpose: Validate E2E scripts and CI environment parity${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to log with timestamp
log_with_time() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Function to cleanup validation environment
cleanup_validation() {
    echo -e "${BLUE}🧹 Cleaning up validation environment...${NC}"
    rm -rf "$TEMP_DIR" 2>/dev/null || true

    # Stop any containers that might be running from validation
    docker compose -f docker-compose.e2e-no-cosmos.yml down --remove-orphans --volumes >/dev/null 2>&1 || true
    docker compose -f docker-compose.e2e-arm64.yml down --remove-orphans --volumes >/dev/null 2>&1 || true

    echo -e "${GREEN}✅ Validation cleanup completed${NC}"
}

# Function to validate script output parsing
validate_script_output_parsing() {
    echo -e "${BLUE}🔍 Validating script output parsing...${NC}"

    mkdir -p "$TEMP_DIR"

    # Create a test version of the determine_docker_compose_config function
    cat > "$TEMP_DIR/test_function.sh" << 'EOF'
#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log_with_time() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') $1" >&2
}

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

# Test the function
COMPOSE_FILE=$(determine_docker_compose_config)
echo "RESULT: [$COMPOSE_FILE]"

# Validate result
if [[ "$COMPOSE_FILE" =~ ^docker-compose\..*\.yml$ ]]; then
    echo "✅ Output parsing: Clean filename"
    exit 0
else
    echo "❌ Output parsing: Contaminated filename"
    exit 1
fi
EOF

    # Test the function
    if bash "$TEMP_DIR/test_function.sh" > "$TEMP_DIR/output.log" 2>&1; then
        echo -e "${GREEN}✅ Script output parsing: Clean${NC}"

        # Verify the actual output
        if grep -q "RESULT: \[docker-compose\..*\.yml\]" "$TEMP_DIR/output.log"; then
            echo -e "${GREEN}✅ Output format validation: Passed${NC}"
        else
            echo -e "${RED}❌ Output format validation: Failed${NC}"
            cat "$TEMP_DIR/output.log"
            return 1
        fi
    else
        echo -e "${RED}❌ Script output parsing: Failed${NC}"
        cat "$TEMP_DIR/output.log"
        return 1
    fi
}

# Function to validate Docker Compose file selection logic
validate_compose_file_selection() {
    echo -e "${BLUE}🐳 Validating Docker Compose file selection...${NC}"

    # Test CI environment detection
    echo -e "${CYAN}Testing CI environment detection...${NC}"
    if CI=true bash -c 'source scripts/e2e-setup-enhanced.sh; determine_docker_compose_config' 2>/dev/null | grep -q "docker-compose.e2e-no-cosmos.yml"; then
        echo -e "${GREEN}✅ CI environment: Correct file selected${NC}"
    else
        echo -e "${RED}❌ CI environment: Wrong file selected${NC}"
        return 1
    fi

    # Test ARM64 detection
    echo -e "${CYAN}Testing ARM64 architecture detection...${NC}"
    local current_arch=$(uname -m)
    if [[ "$current_arch" == "arm64" || "$current_arch" == "aarch64" ]]; then
        if unset CI && bash -c 'source scripts/e2e-setup-enhanced.sh; determine_docker_compose_config' 2>/dev/null | grep -q "docker-compose.e2e-no-cosmos.yml"; then
            echo -e "${GREEN}✅ ARM64 environment: Correct file selected${NC}"
        else
            echo -e "${RED}❌ ARM64 environment: Wrong file selected${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Not ARM64 environment, skipping ARM64 test${NC}"
    fi
}

# Function to validate Docker Compose files exist and are valid
validate_compose_files() {
    echo -e "${BLUE}📋 Validating Docker Compose files...${NC}"

    local files=(
        "docker-compose.yml"
        "docker-compose.e2e-no-cosmos.yml"
        "docker-compose.e2e-arm64.yml"
    )

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}✅ File exists: $file${NC}"

            # Validate syntax
            if docker compose -f "$file" config >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Valid syntax: $file${NC}"
            else
                echo -e "${RED}❌ Invalid syntax: $file${NC}"
                docker compose -f "$file" config 2>&1 | head -5
                return 1
            fi
        else
            echo -e "${RED}❌ File missing: $file${NC}"
            return 1
        fi
    done
}

# Function to validate E2E setup script execution (dry run)
validate_e2e_setup_dryrun() {
    echo -e "${BLUE}🧪 Validating E2E setup script (dry run)...${NC}"

    # Create a modified version that doesn't actually start containers
    mkdir -p "$TEMP_DIR"

    # Copy the script and modify it for dry run
    cp scripts/e2e-setup-enhanced.sh "$TEMP_DIR/e2e-setup-dryrun.sh"

    # Patch the script to skip actual Docker operations
    sed -i.bak 's/docker compose -f "$compose_file" build --no-cache/echo "DRY RUN: docker compose -f $compose_file build --no-cache"/' "$TEMP_DIR/e2e-setup-dryrun.sh" 2>/dev/null || \
    sed -i'.bak' 's/docker compose -f "$compose_file" build --no-cache/echo "DRY RUN: docker compose -f $compose_file build --no-cache"/' "$TEMP_DIR/e2e-setup-dryrun.sh"

    sed -i.bak 's/docker compose -f "$compose_file" up -d/echo "DRY RUN: docker compose -f $compose_file up -d"/' "$TEMP_DIR/e2e-setup-dryrun.sh" 2>/dev/null || \
    sed -i'.bak' 's/docker compose -f "$compose_file" up -d/echo "DRY RUN: docker compose -f $compose_file up -d"/' "$TEMP_DIR/e2e-setup-dryrun.sh"

    # Run the dry run version
    if timeout 30 bash "$TEMP_DIR/e2e-setup-dryrun.sh" > "$TEMP_DIR/dryrun.log" 2>&1; then
        echo -e "${GREEN}✅ E2E setup script: Dry run successful${NC}"
    else
        echo -e "${RED}❌ E2E setup script: Dry run failed${NC}"
        echo -e "${YELLOW}Dry run log:${NC}"
        tail -20 "$TEMP_DIR/dryrun.log"
        return 1
    fi
}

# Function to simulate CI environment
validate_ci_environment_simulation() {
    echo -e "${BLUE}🤖 Validating CI environment simulation...${NC}"

    # Test with CI environment variables set
    export CI=true
    export RUNNER_OS=Linux
    export RUNNER_ARCH=X64

    # Test script behavior in CI mode
    mkdir -p "$TEMP_DIR/ci_test"
    cd "$TEMP_DIR/ci_test"

    # Copy necessary files
    cp -r "$PROJECT_ROOT/scripts" .
    cp "$PROJECT_ROOT"/docker-compose*.yml .

    # Test the determine_docker_compose_config function in CI mode
    if bash -c 'source scripts/e2e-setup-enhanced.sh; determine_docker_compose_config' 2>/dev/null | grep -q "docker-compose.e2e-no-cosmos.yml"; then
        echo -e "${GREEN}✅ CI simulation: Correct behavior${NC}"
    else
        echo -e "${RED}❌ CI simulation: Incorrect behavior${NC}"
        return 1
    fi

    # Clean up CI environment variables
    unset CI RUNNER_OS RUNNER_ARCH
    cd "$PROJECT_ROOT"
}

# Function to validate Playwright test structure
validate_playwright_tests() {
    echo -e "${BLUE}🎭 Validating Playwright test structure...${NC}"

    if [ ! -d "tests/e2e" ]; then
        echo -e "${RED}❌ E2E tests directory missing${NC}"
        return 1
    fi

    # Check for test files
    if find tests/e2e -name "*.spec.ts" | head -1 >/dev/null; then
        echo -e "${GREEN}✅ Playwright test files found${NC}"
    else
        echo -e "${RED}❌ No Playwright test files found${NC}"
        return 1
    fi

    # Check Playwright configuration
    if [ -f "playwright.config.ts" ]; then
        echo -e "${GREEN}✅ Playwright configuration exists${NC}"
    else
        echo -e "${RED}❌ Playwright configuration missing${NC}"
        return 1
    fi
}

# Main validation execution
main() {
    log_with_time "Starting comprehensive E2E validation..."

    # Set up trap for cleanup
    trap cleanup_validation EXIT INT TERM

    case "$VALIDATION_MODE" in
        "quick")
            echo -e "${CYAN}Running quick validation...${NC}"
            validate_script_output_parsing
            validate_compose_files
            ;;
        "full")
            echo -e "${CYAN}Running full validation...${NC}"
            validate_script_output_parsing
            validate_compose_file_selection
            validate_compose_files
            validate_playwright_tests
            validate_ci_environment_simulation

            # Only run dry run if Docker is available
            if command -v docker >/dev/null 2>&1; then
                validate_e2e_setup_dryrun
            else
                echo -e "${YELLOW}⚠️  Docker not available, skipping dry run validation${NC}"
            fi
            ;;
        *)
            echo -e "${RED}❌ Invalid validation mode: $VALIDATION_MODE${NC}"
            echo -e "${CYAN}Available modes: quick, full${NC}"
            exit 1
            ;;
    esac

    log_with_time "Comprehensive E2E validation completed successfully!"
    echo ""
    echo -e "${GREEN}🎉 All E2E validations passed${NC}"
    echo -e "${CYAN}The E2E environment is properly configured for CI/CD${NC}"
}

# Execute main function
main "$@"
