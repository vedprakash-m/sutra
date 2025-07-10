#!/bin/bash

# Cross-Platform CI/CD Validation Script
# Simulates CI environment constraints locally to catch platform-specific issues

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔄 Cross-Platform CI/CD Validation"
echo "=================================="
echo "Project: $(basename "$PROJECT_ROOT")"
echo "Platform: $(uname -s)"
echo "Architecture: $(uname -m)"
echo ""

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation functions
validate_git_tracking() {
    echo -e "${BLUE}🔍 Checking for problematic git tracking...${NC}"
    
    # Check for virtual environments in git
    if git ls-files | grep -E "\.venv|/venv|pyvenv\.cfg" | head -5; then
        echo -e "${RED}❌ Virtual environments found in git tracking${NC}"
        echo "These contain platform-specific symlinks and binaries"
        echo "Run: git rm -r --cached .venv* venv* env*"
        return 1
    fi
    
    # Check for platform-specific binaries
    if git ls-files | grep -E "\.(exe|dll|dylib|so)$" | grep -v node_modules | head -5; then
        echo -e "${RED}❌ Platform-specific binaries found in git${NC}"
        return 1
    fi
    
    # Check for OS-specific paths in files
    if git ls-files -z | xargs -0 grep -l "/Library/Developer\|C:\\\\Program Files\|/usr/local" 2>/dev/null | head -5; then
        echo -e "${YELLOW}⚠️  Files contain OS-specific paths - may cause CI issues${NC}"
        git ls-files -z | xargs -0 grep -l "/Library/Developer\|C:\\\\Program Files\|/usr/local" 2>/dev/null | head -5
    fi
    
    echo -e "${GREEN}✅ Git tracking validation passed${NC}"
}

validate_symlinks_cross_platform() {
    echo -e "${BLUE}🔗 Checking symlinks for cross-platform compatibility...${NC}"
    
    # Find all symlinks
    local broken_symlinks=()
    while IFS= read -r -d '' symlink; do
        if [[ -L "$symlink" && ! -e "$symlink" ]]; then
            broken_symlinks+=("$symlink")
        fi
    done < <(find . -type l -print0 2>/dev/null)
    
    if [[ ${#broken_symlinks[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Broken symlinks detected (will fail in CI):${NC}"
        printf '%s\n' "${broken_symlinks[@]}"
        return 1
    fi
    
    # Check for absolute symlinks (problematic across platforms)
    local absolute_symlinks=()
    while IFS= read -r -d '' symlink; do
        if [[ -L "$symlink" ]]; then
            local target
            target=$(readlink "$symlink")
            if [[ "$target" = /* ]]; then
                absolute_symlinks+=("$symlink -> $target")
            fi
        fi
    done < <(find . -type l -print0 2>/dev/null)
    
    if [[ ${#absolute_symlinks[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Absolute symlinks detected (may fail in CI):${NC}"
        printf '%s\n' "${absolute_symlinks[@]}"
    fi
    
    echo -e "${GREEN}✅ Symlink validation passed${NC}"
}

validate_dependencies_cross_platform() {
    echo -e "${BLUE}📦 Checking dependencies for cross-platform compatibility...${NC}"
    
    # Check package.json for platform-specific dependencies
    if [[ -f "package.json" ]] && jq '.dependencies, .devDependencies' package.json 2>/dev/null | grep -E "win32|darwin|linux" | head -5; then
        echo -e "${YELLOW}⚠️  Platform-specific npm dependencies detected${NC}"
    fi
    
    # Check requirements.txt for platform-specific packages
    find . -name "requirements*.txt" -exec grep -l "win32\|darwin\|linux" {} \; 2>/dev/null || true
    
    echo -e "${GREEN}✅ Dependencies validation passed${NC}"
}

simulate_ci_environment() {
    echo -e "${BLUE}🐳 Simulating CI environment constraints...${NC}"
    
    # Test in isolated environment if Docker available
    if command -v docker &> /dev/null; then
        echo "Testing with Ubuntu environment simulation..."
        
        # Create a minimal test Dockerfile
        cat > /tmp/ci-test.Dockerfile << 'EOF'
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 python3-pip nodejs npm git curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install pre-commit
WORKDIR /workspace
EOF
        
        # Test pre-commit in container
        if docker build -f /tmp/ci-test.Dockerfile -t ci-test-temp /tmp && \
           docker run --rm -v "$PROJECT_ROOT:/workspace" ci-test-temp \
           bash -c "cd /workspace && pre-commit run check-symlinks --all-files"; then
            echo -e "${GREEN}✅ CI environment simulation passed${NC}"
        else
            echo -e "${RED}❌ CI environment simulation failed${NC}"
            return 1
        fi
        
        # Cleanup
        docker rmi ci-test-temp 2>/dev/null || true
        rm -f /tmp/ci-test.Dockerfile
    else
        echo -e "${YELLOW}⚠️  Docker not available, skipping CI simulation${NC}"
    fi
}

run_platform_specific_tests() {
    echo -e "${BLUE}🧪 Running platform-specific validation tests...${NC}"
    
    # Test path separators
    if find . -name "*.json" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l "\\\\\\\\" 2>/dev/null | head -5; then
        echo -e "${YELLOW}⚠️  Windows-style path separators found in config files${NC}"
    fi
    
    # Test line endings (if file command available)
    if command -v file &> /dev/null; then
        local crlf_files=()
        while IFS= read -r -d '' file; do
            if file "$file" | grep -q "CRLF"; then
                crlf_files+=("$file")
            fi
        done < <(find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.sh" \) -print0 2>/dev/null)
        
        if [[ ${#crlf_files[@]} -gt 0 ]]; then
            echo -e "${YELLOW}⚠️  Files with Windows line endings (CRLF) detected:${NC}"
            printf '%s\n' "${crlf_files[@]}" | head -5
        fi
    fi
    
    echo -e "${GREEN}✅ Platform-specific tests completed${NC}"
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    local failed=0
    
    validate_git_tracking || failed=1
    echo ""
    
    validate_symlinks_cross_platform || failed=1
    echo ""
    
    validate_dependencies_cross_platform || failed=1
    echo ""
    
    run_platform_specific_tests || failed=1
    echo ""
    
    # Only run Docker simulation if explicitly requested (slow)
    if [[ "${1:-}" == "--full" ]]; then
        simulate_ci_environment || failed=1
        echo ""
    fi
    
    if [[ $failed -eq 0 ]]; then
        echo -e "${GREEN}🎉 Cross-platform validation PASSED${NC}"
        echo "Code should work correctly in CI environment"
        return 0
    else
        echo -e "${RED}💥 Cross-platform validation FAILED${NC}"
        echo "Issues detected that will likely cause CI failures"
        return 1
    fi
}

# Show usage if requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Cross-Platform CI/CD Validation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full    Run full validation including Docker simulation (slow)"
    echo "  --help    Show this help message"
    echo ""
    echo "This script detects platform-specific issues that cause CI failures"
    echo "Run before pushing to catch problems early"
    exit 0
fi

main "$@"
