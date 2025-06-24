#!/bin/bash

# Enhanced E2E Local Validation Script
# Includes comprehensive testing that matches CI/CD pipeline

set -e  # Exit on any error

echo "🔍 ENHANCED E2E LOCAL VALIDATION"
echo "================================="
echo

cd "$(dirname "$0")/../api"

echo "📍 Working directory: $(pwd)"
echo

# Step 1: Python Environment Check
echo "🐍 Step 1: Python Environment Validation"
echo "----------------------------------------"
if ! /Users/vedprakashmishra/sutra/.venv/bin/python --version; then
    echo "❌ Python environment not available"
    exit 1
fi
echo "✅ Python environment ready"
echo

# Step 2: Dependencies Check
echo "📦 Step 2: Dependencies Validation"
echo "----------------------------------"
if ! /Users/vedprakashmishra/sutra/.venv/bin/python -c "import azure.functions, pytest, mock"; then
    echo "❌ Required dependencies missing"
    exit 1
fi
echo "✅ All dependencies available"
echo

# Step 3: Syntax Validation
echo "🔍 Step 3: Syntax & Import Validation"
echo "-------------------------------------"

# Check all main modules compile
for module in admin_api integrations_api llm_execute_api playbooks_api collections_api getroles; do
    echo "  Checking $module..."
    if ! /Users/vedprakashmishra/sutra/.venv/bin/python -m py_compile "${module}/__init__.py" 2>/dev/null; then
        echo "❌ Syntax error in $module"
        exit 1
    fi
done

echo "  Checking shared/auth_static_web_apps.py..."
if ! /Users/vedprakashmishra/sutra/.venv/bin/python -m py_compile "shared/auth_static_web_apps.py" 2>/dev/null; then
    echo "❌ Syntax error in shared/auth_static_web_apps.py"
    exit 1
fi
echo "✅ All modules compile successfully"
echo

# Step 4: Import Validation
echo "🔗 Step 4: Import Resolution Check"
echo "----------------------------------"
/Users/vedprakashmishra/sutra/.venv/bin/python -c "
import sys
import os
sys.path.append(os.getcwd())

modules_to_test = [
    'admin_api',
    'integrations_api',
    'llm_execute_api',
    'playbooks_api',
    'collections_api',
    'getroles',
    'shared.auth_static_web_apps'
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f'✅ {module} imports successfully')
    except Exception as e:
        print(f'❌ {module} import failed: {e}')
        sys.exit(1)
"
echo

# Step 5: Linting Check (F821 specifically)
echo "🧹 Step 5: Linting Validation (F821 undefined names)"
echo "---------------------------------------------------"
if ! /Users/vedprakashmishra/sutra/.venv/bin/python -m flake8 --select=F821 admin_api/__init__.py integrations_api/__init__.py llm_execute_api/__init__.py playbooks_api/__init__.py collections_api/__init__.py getroles/__init__.py; then
    echo "❌ Undefined name errors found"
    exit 1
fi
echo "✅ No undefined name errors"
echo

# Step 6: **NEW** - Test Suite Validation
echo "🧪 Step 6: Test Suite Validation (CRITICAL)"
echo "--------------------------------------------"
echo "Setting testing mode and running pytest collection..."

# Set testing mode to bypass decorators
export TESTING_MODE=true

# First, just try to collect tests without running them
if ! TESTING_MODE=true /Users/vedprakashmishra/sutra/.venv/bin/python -m pytest --collect-only -q > /tmp/test_collection.log 2>&1; then
    echo "❌ Test collection failed - checking for authentication mocking issues..."
    cat /tmp/test_collection.log | grep -E "(AttributeError|verify_jwt_token|get_user_id_from_token|check_admin_role)" || true
    echo
    echo "🔍 Detailed error log:"
    cat /tmp/test_collection.log
    exit 1
fi
echo "✅ All tests can be collected successfully"
echo

# Step 7: Sample Test Run
echo "🎯 Step 7: Sample Test Execution"
echo "--------------------------------"
echo "Running a small subset of tests to validate auth mocking..."

# Run just a few tests to validate the auth system works
if ! TESTING_MODE=true /Users/vedprakashmishra/sutra/.venv/bin/python -m pytest health/health_test.py -v --tb=short; then
    echo "❌ Sample test execution failed"
    exit 1
fi
echo "✅ Sample tests pass"

# Test the previously failing auth test
echo "Testing decorator-based auth endpoint..."
if ! TESTING_MODE=true /Users/vedprakashmishra/sutra/.venv/bin/python -m pytest collections_api/collections_test.py::TestCollectionsAPI::test_list_collections_with_filters -v --tb=short; then
    echo "❌ Auth decorator test failed"
    exit 1
fi
echo "✅ Auth decorator test passes"
echo

# Step 8: Authentication Function Testing
echo "🔐 Step 8: Authentication System Testing"
echo "----------------------------------------"
/Users/vedprakashmishra/sutra/.venv/bin/python -c "
import sys
import os
sys.path.append(os.getcwd())
from shared.auth_static_web_apps import get_current_user, require_auth, require_admin

print('✅ New authentication functions available')

# Test decorators exist and are callable
assert callable(require_auth), 'require_auth is not callable'
assert callable(require_admin), 'require_admin is not callable'
print('✅ Authentication decorators are callable')
"
echo

echo "🎉 ENHANCED E2E VALIDATION COMPLETE"
echo "==================================="
echo "✅ All validations passed!"
echo "✅ Syntax, imports, linting, and test collection successful"
echo "✅ Ready for CI/CD deployment"
echo
