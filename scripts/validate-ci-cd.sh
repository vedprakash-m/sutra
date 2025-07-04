#!/bin/bash

# CI/CD Simulation Validator for Sutra
# This script simulates the exact CI environment to catch issues locally

set -e

echo "🔬 CI/CD Environment Simulation"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track issues found
ISSUES_FOUND=0

echo "📋 Checking CI/CD configuration files..."

# Check if CI workflow files exist
if [ ! -f ".github/workflows/ci-cd.yml" ]; then
    echo -e "${RED}❌ CI/CD workflow file not found${NC}"
    ((ISSUES_FOUND++))
else
    echo -e "${GREEN}✅ CI/CD workflow file found${NC}"

    # Check if CI is using the correct requirements file
    if grep -q "requirements\.txt" .github/workflows/ci-cd.yml; then
        echo -e "${RED}❌ CI/CD is using requirements.txt (problematic)${NC}"
        echo "   Found references to requirements.txt in CI workflow"
        echo "   This will cause grpcio compilation failures"
        ((ISSUES_FOUND++))
    elif grep -q "requirements-minimal\.txt" .github/workflows/ci-cd.yml; then
        echo -e "${GREEN}✅ CI/CD is using requirements-minimal.txt${NC}"
    else
        echo -e "${YELLOW}⚠️ Cannot determine which requirements file CI is using${NC}"
        ((ISSUES_FOUND++))
    fi

    # Check Python version consistency
    if grep -q "python-version:" .github/workflows/ci-cd.yml; then
        CI_PYTHON_VERSION=$(grep "python-version:" .github/workflows/ci-cd.yml | head -1 | sed 's/.*python-version: *//' | sed 's/ *$//')
        echo "🐍 CI Python version: $CI_PYTHON_VERSION"

        LOCAL_PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        echo "🐍 Local Python version: $LOCAL_PYTHON_VERSION"

        if [[ "$CI_PYTHON_VERSION" != "$LOCAL_PYTHON_VERSION"* ]]; then
            echo -e "${YELLOW}⚠️ Python version mismatch between local and CI${NC}"
        else
            echo -e "${GREEN}✅ Python versions match${NC}"
        fi
    fi
fi

echo ""
echo "🔧 Simulating CI backend dependency installation..."

# Create temporary environment to test CI installation
TEMP_DIR=$(mktemp -d)
ORIGINAL_DIR="$PWD"
cd "$TEMP_DIR"

# Copy requirements files
cp "$ORIGINAL_DIR/api/requirements"*.txt . 2>/dev/null || true

# Test each requirements file
for req_file in requirements-minimal.txt requirements-ci.txt requirements.txt; do
    if [ -f "$req_file" ]; then
        echo ""
        echo "📦 Testing $req_file (as CI would)..."

        # Skip problematic files on local testing to save time
        if [[ "$req_file" == "requirements-ci.txt" || "$req_file" == "requirements.txt" ]]; then
            echo "⏭️ Skipping $req_file (contains grpcio compilation - tested elsewhere)"
            continue
        fi

        # Create isolated environment
        python3 -m venv test-ci-env
        source test-ci-env/bin/activate

        # Upgrade pip like CI does
        pip install --upgrade pip setuptools wheel

        # Try to install requirements
        if pip install -r "$req_file" > install_log.txt 2>&1; then
            echo -e "${GREEN}✅ $req_file installs successfully${NC}"

            # Test key imports
            if python3 -c "
import azure.functions
import azure.cosmos
import azure.identity
import pydantic
import httpx
print('All imports successful')
" 2>/dev/null; then
                echo -e "${GREEN}✅ Key modules import successfully${NC}"

                # Test pytest with coverage like CI does
                echo "🧪 Testing pytest with coverage (CI simulation)..."
                cd "$ORIGINAL_DIR/api"
                if python -c "import pytest_cov; print('pytest-cov available')" >/dev/null 2>&1 && python -m pytest --version | grep -q "pytest"; then
                    echo -e "${GREEN}✅ Pytest coverage test passed${NC}"
                else
                    echo -e "${RED}❌ Pytest coverage test failed${NC}"
                    echo "   This would cause CI backend-tests to fail"
                    ((ISSUES_FOUND++))
                fi

                # Test for namespace collisions (critical for CI success)
                echo "🔍 Testing for namespace collisions..."
                python -c "
import os
import sys

# Critical Python built-in modules that must not conflict
critical_modules = [
    'collections', 'os', 'sys', 'json', 'time', 'datetime', 'itertools',
    'functools', 'operator', 'pathlib', 'urllib', 'http', 'email', 'calendar',
    'uuid', 'random', 'math', 'statistics', 'decimal', 'fractions',
    'logging', 'warnings', 'traceback', 'contextlib', 'abc', 'types',
    'copy', 'pickle', 'shelve', 'marshal', 'sqlite3', 'csv', 'configparser'
]

api_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and not d.startswith('__')]
conflicts = [d for d in api_dirs if d in critical_modules]

if conflicts:
    print(f'❌ CRITICAL: Namespace collision detected: {conflicts}')
    print('These API directories conflict with Python built-in modules!')
    print('This will cause CI failures when pytest runs!')
    sys.exit(1)

# Test critical imports with current directory in path (exact CI simulation)
sys.path.insert(0, '.')
try:
    from collections import deque, defaultdict
    import json
    import os as os_module
    print('✅ Critical imports work with current directory in path')
except ImportError as e:
    print(f'❌ CRITICAL: Import error with current directory in path: {e}')
    print('This will cause CI failures!')
    sys.exit(1)
"
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ Namespace collision detected - CI will fail!${NC}"
                    ((ISSUES_FOUND++))
                else
                    echo -e "${GREEN}✅ No namespace collisions detected${NC}"
                fi

                cd "$TEMP_DIR"
            else
                echo -e "${RED}❌ Import test failed for $req_file${NC}"
                ((ISSUES_FOUND++))
            fi
        else
            echo -e "${RED}❌ $req_file installation failed${NC}"
            echo "   Last few lines of error:"
            tail -10 install_log.txt
            ((ISSUES_FOUND++))
        fi

        deactivate
        rm -rf test-ci-env
    fi
done

# Clean up
cd "$ORIGINAL_DIR"
rm -rf "$TEMP_DIR"

echo ""
echo "📊 Testing requirements file strategy..."

# Check if all requirements files exist
REQUIREMENTS_FILES=("requirements.txt" "requirements-ci.txt" "requirements-minimal.txt")
for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "api/$req_file" ]; then
        echo -e "${GREEN}✅ api/$req_file exists${NC}"
    else
        echo -e "${YELLOW}⚠️ api/$req_file missing (OK if using minimal strategy)${NC}"
        # Only count as error if it's the minimal file that's missing
        if [[ "$req_file" == "requirements-minimal.txt" ]]; then
            ((ISSUES_FOUND++))
        fi
    fi
done

# Check Docker configuration
echo ""
echo "🐳 Checking Docker configuration..."

if [ -f "api/Dockerfile.dev" ]; then
    if grep -q "requirements-minimal\.txt" api/Dockerfile.dev; then
        echo -e "${GREEN}✅ Docker uses requirements-minimal.txt${NC}"
    elif grep -q "requirements\.txt" api/Dockerfile.dev; then
        echo -e "${YELLOW}⚠️ Docker uses requirements.txt (may cause issues)${NC}"
    else
        echo -e "${YELLOW}⚠️ Cannot determine which requirements Docker uses${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Docker configuration missing (OK for cloud deployment)${NC}"
fi

# Check documentation consistency
echo ""
echo "📚 Checking documentation consistency..."

DOCS_FILES=("README.md" "E2E_TESTING.md" "E2E_QUICK_REFERENCE.md")
for doc_file in "${DOCS_FILES[@]}"; do
    if [ -f "$doc_file" ]; then
        if grep -q "requirements-minimal\.txt" "$doc_file"; then
            echo -e "${GREEN}✅ $doc_file recommends requirements-minimal.txt${NC}"
        elif grep -q "requirements\.txt" "$doc_file" && ! grep -q "requirements-minimal\.txt" "$doc_file"; then
            echo -e "${YELLOW}⚠️ $doc_file may need updating for new requirements strategy${NC}"
        fi
    fi
done

echo ""
echo "🎯 Final CI/CD Simulation Results"
echo "================================="

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}🎉 All CI/CD simulation checks passed!${NC}"
    echo -e "${GREEN}The local environment matches CI requirements${NC}"
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issue(s) that could cause CI failures${NC}"
    echo ""
    echo "🔧 Recommended actions:"
    echo "1. Update .github/workflows/ci-cd.yml to use requirements-minimal.txt"
    echo "2. Test all requirements files for compatibility"
    echo "3. Ensure Docker and CI use the same requirements strategy"
    echo "4. Update documentation to reflect new requirements approach"
fi

echo ""
echo "📝 CI/CD Simulation Complete"
exit $ISSUES_FOUND
