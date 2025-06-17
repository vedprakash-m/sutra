#!/bin/bash

# Backend Dependencies Testing Script for Sutra
# Tests that all backend dependencies are correctly installed and working

set -e

echo "🧪 Backend Dependencies Test"
echo "============================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track issues found
ISSUES_FOUND=0

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/api"

echo "📍 Project root: $PROJECT_ROOT"
echo "📍 API directory: $API_DIR"

# Check if we're in the right place
if [ ! -d "$API_DIR" ]; then
    echo -e "${RED}❌ API directory not found at $API_DIR${NC}"
    exit 1
fi

echo ""
echo "🔍 Checking Python environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python version: $PYTHON_VERSION"

# Change to API directory for testing
cd "$API_DIR"

echo ""
echo "📦 Checking requirements files..."

# Check which requirements files exist
for req_file in requirements-minimal.txt requirements-ci.txt requirements.txt; do
    if [ -f "$req_file" ]; then
        echo -e "${GREEN}✅ $req_file found${NC}"
    else
        echo -e "${YELLOW}⚠️ $req_file not found${NC}"
    fi
done

echo ""
echo "🧪 Testing critical imports..."

# Test critical imports that are used in the application
python3 -c "
import sys
import traceback

critical_imports = [
    'azure.functions',
    'azure.cosmos', 
    'azure.identity',
    'pydantic',
    'httpx',
    'pytest',
    'pytest_cov'
]

failed_imports = []

for module in critical_imports:
    try:
        __import__(module)
        print(f'✅ {module} imported successfully')
    except ImportError as e:
        print(f'❌ {module} import failed: {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'\\n❌ CRITICAL: {len(failed_imports)} imports failed!')
    print('Missing modules:', ', '.join(failed_imports))
    sys.exit(1)
else:
    print('\\n✅ All critical imports successful')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Critical import test failed${NC}"
    ((ISSUES_FOUND++))
else
    echo -e "${GREEN}✅ Critical import test passed${NC}"
fi

echo ""
echo "🔧 Testing pytest with coverage (CI simulation)..."

# Test pytest-cov availability and functionality
python3 -c "
import pytest_cov
import pytest
print('pytest-cov version:', pytest_cov.__version__)
print('pytest version:', pytest.__version__)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ pytest-cov not available${NC}"
    echo "   This will cause CI backend-tests to fail with:"
    echo "   ERROR: unrecognized arguments: --cov=. --cov-report=xml"
    ((ISSUES_FOUND++))
else
    echo -e "${GREEN}✅ pytest-cov is available${NC}"
    
    # Test the exact command used in CI
    echo "🧪 Testing CI coverage command: pytest --cov=. --cov-report=xml --version"
    if python3 -m pytest --cov=. --cov-report=xml --version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ CI coverage command works${NC}"
    else
        echo -e "${RED}❌ CI coverage command failed${NC}"
        echo "   The command 'pytest --cov=. --cov-report=xml' will fail in CI"
        ((ISSUES_FOUND++))
    fi
fi

echo ""
echo "🔍 Testing for namespace collisions..."

# Test for namespace collisions with Python built-in modules
# This simulates the exact environment that CI runs in
python3 -c "
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

# Check for conflicting directories
api_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and not d.startswith('__')]
conflicts = [d for d in api_dirs if d in critical_modules]

if conflicts:
    print(f'❌ CRITICAL: Namespace collision detected: {conflicts}')
    print('These API directories conflict with Python built-in modules!')
    print('This will cause import errors when pytest runs from the api directory!')
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

echo ""
echo "📊 Backend Dependencies Test Results"
echo "===================================="

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}🎉 All backend dependency tests passed!${NC}"
    echo -e "${GREEN}Backend is ready for CI/CD${NC}"
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issue(s) in backend dependencies${NC}"
    echo ""
    echo "🔧 Recommended actions:"
    echo "1. Install missing packages with: pip install -r requirements-minimal.txt"
    echo "2. Remove any conflicting directories that shadow Python built-ins"
    echo "3. Ensure pytest-cov is installed for coverage testing"
fi

echo ""
echo "📝 Backend Dependencies Test Complete"
exit $ISSUES_FOUND
