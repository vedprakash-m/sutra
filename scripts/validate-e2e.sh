#!/bin/bash

# E2E Testing Validation Script for Sutra
# This script validates the E2E testing setup

set -e

echo "🧪 Sutra E2E Testing Validation"
echo "==============================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    echo "✅ npm: $(npm --version)"
else
    echo "❌ npm not found"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose (legacy): $(docker-compose --version)"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker Desktop"
    exit 1
fi

echo ""
echo "🔧 Validating project configuration..."

# Validate package.json scripts
if npm run --silent > /dev/null 2>&1; then
    echo "✅ package.json scripts are valid"
else
    echo "❌ package.json scripts validation failed"
    exit 1
fi

# Check if Playwright is installed
if npx playwright --version &> /dev/null; then
    echo "✅ Playwright: $(npx playwright --version)"
else
    echo "⚠️ Playwright not found. Installing..."
    npm ci
    npx playwright install
fi

# Check backend dependencies
echo "🐍 Checking backend dependencies..."
cd api
if python3 -c "import azure.functions" &> /dev/null; then
    echo "✅ Backend dependencies are installed"
else
    echo "⚠️ Backend dependencies not found. Installing..."
    # Try CI requirements first to avoid grpcio compilation issues
    if pip install -r requirements-ci.txt; then
        echo "✅ Backend dependencies installed successfully (using CI requirements)"
    else
        echo "❌ Failed to install backend dependencies"
        echo "💡 Try running: cd api && pip install -r requirements-ci.txt"
        cd ..
        exit 1
    fi
fi
cd ..

# Validate Docker Compose configuration
echo "🐳 Validating Docker Compose configuration..."
if docker compose config &> /dev/null; then
    echo "✅ docker-compose.yml is valid"
elif docker-compose config &> /dev/null; then
    echo "✅ docker-compose.yml is valid (legacy CLI)"
else
    echo "❌ docker-compose.yml configuration is invalid"
    exit 1
fi

# Validate Playwright configuration
echo "🎭 Validating Playwright configuration..."
if npx playwright test --list &> /dev/null; then
    echo "✅ Playwright configuration is valid"
    TEST_COUNT=$(npx playwright test --list | wc -l)
    echo "   Found $TEST_COUNT test files"
else
    echo "❌ Playwright configuration is invalid"
    exit 1
fi

# Run linting
echo "🔍 Running code quality checks..."
if npm run lint; then
    echo "✅ Linting passed"
else
    echo "❌ Linting failed"
    exit 1
fi

# Run type checking
if npm run type-check; then
    echo "✅ Type checking passed"
else
    echo "❌ Type checking failed"
    exit 1
fi

echo ""
echo "🚀 Running E2E workflow test..."

# Test the E2E setup (without actually running tests)
echo "📦 Testing service startup..."
if docker compose up -d --build; then
    echo "✅ Services started successfully"
    
    # Wait a moment for services to initialize
    sleep 10
    
    # Check service health
    echo "🔍 Checking service health..."
    
    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        echo "✅ Services are running"
    else
        echo "❌ Some services failed to start"
        docker compose logs
        docker compose down
        exit 1
    fi
    
    # Test if frontend is responding
    if curl -s http://localhost:3000 > /dev/null; then
        echo "✅ Frontend is responding on port 3000"
    else
        echo "⚠️ Frontend not yet responding (may need more time)"
    fi
    
    # Test if API is responding
    if curl -s http://localhost:7071/api/health > /dev/null; then
        echo "✅ API is responding on port 7071"
    else
        echo "⚠️ API not yet responding (may need more time)"
    fi
    
    echo "🧹 Cleaning up test services..."
    docker compose down
    echo "✅ Services stopped successfully"
    
else
    echo "❌ Failed to start services"
    exit 1
fi

echo ""
echo "🎉 E2E Testing Validation Complete!"
echo ""
echo "✅ All prerequisites are installed"
echo "✅ Configuration files are valid"
echo "✅ Code quality checks pass"
echo "✅ Services can start and stop properly"
echo ""
echo "Your E2E testing environment is ready!"
echo ""
echo "Next steps:"
echo "  npm run test:e2e        # Run full E2E test suite"
echo "  npm run test:e2e:ui     # Run with interactive UI"
echo "  npm run e2e:setup       # Start services for development"
echo ""
echo "For detailed documentation, see: E2E_TESTING.md"
