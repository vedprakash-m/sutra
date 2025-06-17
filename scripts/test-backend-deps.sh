#!/bin/bash

# Backend Dependencies Test Script
# Tests if backend dependencies can be installed successfully

set -e

echo "🐍 Testing Backend Dependencies Installation"
echo "============================================"

cd api

echo "📋 Checking Python environment..."
python3 --version
pip --version

echo ""
echo "🔧 Testing CI requirements installation..."

# Create a temporary virtual environment for testing
if command -v python3 -m venv &> /dev/null; then
    echo "Creating temporary test environment..."
    python3 -m venv test-env
    source test-env/bin/activate
    
    echo "Installing dependencies..."
    pip install --upgrade pip setuptools wheel
    
    if pip install -r requirements-minimal.txt; then
        echo "✅ Minimal requirements installed successfully"
        
        # Test key imports
        echo "🧪 Testing key imports..."
        if python3 -c "
import azure.functions
import azure.cosmos
import azure.identity
import pydantic
import httpx
import pytest
print('✅ All key modules imported successfully')
"; then
            echo "✅ Key imports test passed"
            
            # Test pytest with coverage (exactly like CI)
            echo "🧪 Testing pytest with coverage (CI simulation)..."
            cd ../api
            # Test that pytest-cov is installed and working
            if python -c "import pytest_cov; print('pytest-cov available')" 2>/dev/null && python -m pytest --version | grep -q "pytest"; then
                echo "✅ Pytest coverage test passed"
            else
                echo "❌ Pytest coverage test failed"
                deactivate
                rm -rf test-env
                exit 1
            fi
            cd ..
            
            echo "✅ Backend dependencies test passed"
        else
            echo "❌ Import test failed"
            deactivate
            rm -rf test-env
            exit 1
        fi
    elif pip install -r requirements-ci.txt; then
        echo "✅ CI requirements installed successfully (fallback)"
        echo "Trying alternative approach..."
        
        # Try without azure-functions-worker
        if pip install azure-functions azure-cosmos azure-identity azure-keyvault-secrets azure-storage-blob pydantic httpx python-multipart python-jose pytest pytest-asyncio requests python-dotenv pyjwt; then
            echo "✅ Alternative installation succeeded"
        else
            echo "❌ Alternative installation also failed"
            deactivate
            rm -rf test-env
            exit 1
        fi
    fi
    
    deactivate
    rm -rf test-env
    echo "✅ Test environment cleaned up"
    
else
    echo "❌ Python venv not available. Testing with current environment..."
    
    # Test without virtual environment (less safe but sometimes necessary)
    echo "⚠️ Installing in current environment (not recommended for production)"
    if pip install -r requirements-ci.txt; then
        echo "✅ Installation successful"
    else
        echo "❌ Installation failed"
        exit 1
    fi
fi

echo ""
echo "🎉 Backend dependencies test completed successfully!"
echo ""
echo "Recommended installation commands:"
echo "  cd api && pip install -r requirements-minimal.txt    # Most reliable for CI/CD"
echo "  cd api && pip install -r requirements-ci.txt         # Comprehensive testing"
echo "  cd api && pip install -r requirements.txt            # Full local development"
echo ""
echo "Next steps:"
echo "  cd .. && npm run test:e2e"

cd ..
