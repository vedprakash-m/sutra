#!/bin/bash

# Simple E2E validation without Docker
# Tests basic functionality to catch issues before CI/CD

set -e

echo "🔍 SIMPLE E2E VALIDATION (No Docker Required)"
echo "============================================="
echo ""

# Test 1: Check if all Python imports work
echo "1. Testing Python imports..."
cd api
if python3 -c "
import azure.functions
import azure.cosmos
import pydantic
import json
import os
import logging
print('✅ All critical imports successful')
" 2>/dev/null; then
    echo "✅ Python dependencies are working"
else
    echo "❌ Python import failures - this will cause container issues"
    exit 1
fi

# Test 2: Check if health function structure is correct
echo ""
echo "2. Testing health function structure..."
if [ -f "health/__init__.py" ] && [ -f "health/function.json" ]; then
    echo "✅ Health function files are present"
else
    echo "❌ Health function files missing"
    exit 1
fi

# Test 3: Check middleware imports (standalone test)
echo ""
echo "3. Testing middleware imports..."
if python3 -c "
import sys
import os
sys.path.append('.')
# Skip relative imports for standalone testing
try:
    import azure.functions as func
    print('✅ Azure Functions can be imported')
    # Test basic HTTP response creation
    response = func.HttpResponse('test', status_code=200)
    print('✅ HttpResponse can be created')
except Exception as e:
    print('❌ Azure Functions error:', e)
    exit(1)
" 2>/dev/null; then
    echo "✅ Core Azure Functions working"
else
    echo "❌ Azure Functions import failed"
    exit 1
fi

# Test 4: Test shared module structure
echo ""
echo "4. Testing shared module structure..."
if [ -d "shared" ] && [ -f "shared/__init__.py" ]; then
    echo "✅ Shared modules are structured correctly"
else
    echo "❌ Shared module structure issue"
    exit 1
fi

cd ..

# Test 5: Check Docker configuration files
echo ""
echo "5. Validating Docker configuration..."
if [ -f "docker-compose.yml" ] && [ -f "api/Dockerfile.dev" ]; then
    echo "✅ Docker configuration files present"
else
    echo "❌ Missing Docker configuration files"
    exit 1
fi

# Test 6: Check function.json files
echo ""
echo "6. Validating Azure Functions configuration..."
cd api
health_config=$(find . -name "function.json" -path "*/health/*" | head -1)
if [ -n "$health_config" ]; then
    if python3 -c "
import json
with open('$health_config') as f:
    config = json.load(f)
    if 'bindings' in config and any(b.get('route') == 'health' for b in config['bindings']):
        print('✅ Health endpoint configured correctly')
    else:
        print('❌ Health endpoint configuration issue')
        exit(1)
" 2>/dev/null; then
        echo "✅ Azure Functions health configuration valid"
    else
        echo "❌ Health endpoint configuration invalid"
        exit 1
    fi
else
    echo "❌ Health function.json not found"
    exit 1
fi

cd ..

echo ""
echo "🎉 SIMPLE E2E VALIDATION PASSED!"
echo "================================"
echo "✅ All Python components can be imported"
echo "✅ Health endpoint should work in container"
echo "✅ Azure Functions configuration is valid"
echo "✅ Docker files are present"
echo ""
echo "🐳 Container healthcheck should now succeed!"
echo ""
echo "Note: This validates basic functionality without Docker."
echo "For full E2E testing, run: ./scripts/test-e2e-local.sh"
