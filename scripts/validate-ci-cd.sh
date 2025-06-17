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
cd "$TEMP_DIR"

# Copy requirements files
cp "$OLDPWD/api/requirements"*.txt . 2>/dev/null || true

# Test each requirements file
for req_file in requirements*.txt; do
    if [ -f "$req_file" ]; then
        echo ""
        echo "📦 Testing $req_file (as CI would)..."
        
        # Create isolated environment
        python3 -m venv test-ci-env
        source test-ci-env/bin/activate
        
        # Upgrade pip like CI does
        pip install --upgrade pip setuptools wheel
        
        # Try to install requirements with timeout (like CI) - reduced timeout for local testing
        timeout 120 pip install -r "$req_file" > install_log.txt 2>&1
        
        if [ $? -eq 0 ]; then
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
            else
                echo -e "${RED}❌ Import test failed for $req_file${NC}"
                ((ISSUES_FOUND++))
            fi
        elif [ $? -eq 124 ]; then
            echo -e "${RED}❌ $req_file installation timed out (>5 min)${NC}"
            echo "   This indicates compilation issues (like grpcio)"
            ((ISSUES_FOUND++))
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
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo ""
echo "📊 Testing requirements file strategy..."

# Check if all requirements files exist
REQUIREMENTS_FILES=("requirements.txt" "requirements-ci.txt" "requirements-minimal.txt")
for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "api/$req_file" ]; then
        echo -e "${GREEN}✅ api/$req_file exists${NC}"
    else
        echo -e "${RED}❌ api/$req_file missing${NC}"
        ((ISSUES_FOUND++))
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
    echo -e "${RED}❌ Docker configuration missing${NC}"
    ((ISSUES_FOUND++))
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
