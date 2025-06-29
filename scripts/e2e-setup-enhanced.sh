#!/bin/bash

# Enhanced E2E Setup Script - Apple Silicon Compatible
# This script detects the platform and chooses the best configuration

set -e

echo "🐳 Starting E2E services..."

# Detect platform
ARCH=$(uname -m)
OS=$(uname -s)

echo "🔍 Detected platform: $OS on $ARCH"

# Setup E2E-specific configuration
echo "📝 Setting up E2E configuration..."
if [ -f "api/local.settings.json.e2e" ]; then
    cp api/local.settings.json api/local.settings.json.backup 2>/dev/null || true
    cp api/local.settings.json.e2e api/local.settings.json
    echo "✅ E2E configuration applied"
else
    echo "⚠️  Warning: api/local.settings.json.e2e not found, using existing config"
fi

# Function to run docker compose with fallback
run_docker_compose() {
    local compose_file="$1"
    local cmd="$2"

    # Try modern docker compose first (preferred in CI/CD)
    if docker compose version >/dev/null 2>&1; then
        echo "Using 'docker compose' (modern)"
        docker compose -f "$compose_file" $cmd
    # Fall back to legacy docker-compose
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "Using 'docker-compose' (legacy)"
        docker-compose -f "$compose_file" $cmd
    else
        echo "❌ Neither 'docker compose' nor 'docker-compose' is available"
        echo "Please install Docker Compose"
        exit 1
    fi
}

# Choose the right Docker Compose file based on platform and preference
choose_compose_file() {
    local force_no_cosmos="${1:-false}"

    if [[ "$force_no_cosmos" == "true" ]]; then
        echo "docker-compose.e2e-no-cosmos.yml"
        return
    fi

    if [[ "$ARCH" == "arm64" && "$OS" == "Darwin" ]]; then
        echo "🍎 Apple Silicon detected"

        # Check if user wants to try Cosmos with ARM64 workarounds
        if [[ "${E2E_TRY_COSMOS:-}" == "true" ]]; then
            echo "🧪 Attempting Cosmos emulator with ARM64 workarounds..."
            echo "docker-compose.e2e-arm64.yml"
        else
            echo "🚀 Using configuration without Cosmos emulator for better ARM64 compatibility"
            echo "docker-compose.e2e-no-cosmos.yml"
        fi
    else
        echo "💻 Using standard E2E configuration"
        echo "docker-compose.yml"
    fi
}

# Get the appropriate compose file
COMPOSE_FILE=$(choose_compose_file "${E2E_NO_COSMOS:-false}")
echo "📄 Using compose file: $COMPOSE_FILE"

# Check if the chosen compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "❌ Compose file $COMPOSE_FILE not found"
    if [[ "$COMPOSE_FILE" == "docker-compose.yml" ]]; then
        echo "💡 Falling back to no-cosmos configuration"
        COMPOSE_FILE="docker-compose.e2e-no-cosmos.yml"
    else
        echo "💡 Falling back to standard configuration"
        COMPOSE_FILE="docker-compose.yml"
    fi
fi

# Start services with retry logic
MAX_RETRIES=3
RETRY_COUNT=0

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    echo "🚀 Attempt $((RETRY_COUNT + 1)) of $MAX_RETRIES to start services..."

    if run_docker_compose "$COMPOSE_FILE" "up -d --build"; then
        echo "✅ E2E services started successfully with $COMPOSE_FILE"

        # Wait for services to be healthy
        echo "⏳ Waiting for services to be ready..."
        sleep 10

        # Check if functions API is responding
        echo "🔍 Checking API health..."
        if curl -f http://localhost:7071/api/health --max-time 10 >/dev/null 2>&1; then
            echo "✅ API is healthy and ready"
            break
        else
            echo "⚠️  API not responding, checking service status..."
            run_docker_compose "$COMPOSE_FILE" "ps"
        fi

        break
    else
        echo "❌ Failed to start services with $COMPOSE_FILE"
        RETRY_COUNT=$((RETRY_COUNT + 1))

        if [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; then
            if [[ "$COMPOSE_FILE" == "docker-compose.e2e-arm64.yml" ]]; then
                echo "💡 Retrying with no-cosmos configuration..."
                COMPOSE_FILE="docker-compose.e2e-no-cosmos.yml"
            elif [[ "$COMPOSE_FILE" == "docker-compose.yml" ]]; then
                echo "💡 Retrying with no-cosmos configuration..."
                COMPOSE_FILE="docker-compose.e2e-no-cosmos.yml"
            fi

            echo "🔄 Cleaning up before retry..."
            run_docker_compose "$COMPOSE_FILE" "down" 2>/dev/null || true
            sleep 5
        fi
    fi
done

if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
    echo "❌ Failed to start E2E services after $MAX_RETRIES attempts"
    echo "🔍 Final service status:"
    run_docker_compose "$COMPOSE_FILE" "ps"
    echo ""
    echo "📋 Troubleshooting tips:"
    echo "1. For Apple Silicon: set E2E_TRY_COSMOS=true to attempt Cosmos with workarounds"
    echo "2. Set E2E_NO_COSMOS=true to skip Cosmos emulator entirely"
    echo "3. Check Docker logs: docker compose -f $COMPOSE_FILE logs"
    echo "4. Try the test configuration: docker compose -f docker-compose.test.yml up -d"
    exit 1
fi

# Validate backend test collection
echo ""
echo "🔍 Validating backend test collection..."
cd api 2>/dev/null || {
    echo "⚠️  Warning: Could not find api directory for backend validation"
}

if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || true
fi

if python -m pytest --collect-only -q > /dev/null 2>&1; then
    echo "✅ Backend test collection validated"
else
    echo "❌ Backend test collection failed - import errors detected"
    echo "🔧 Run 'cd api && python -m pytest --collect-only' to see details"
fi

cd .. 2>/dev/null || true

echo ""
echo "🎉 E2E environment ready!"
echo "📊 Service endpoints:"
echo "   - Frontend: http://localhost:5173"
echo "   - API: http://localhost:7071"
echo "   - Azurite: http://localhost:10000"
if [[ "$COMPOSE_FILE" == *"arm64"* ]]; then
    echo "   - Cosmos Emulator: http://localhost:8081"
fi
echo ""
echo "🔧 Environment configuration:"
echo "   - Compose file: $COMPOSE_FILE"
echo "   - Platform: $OS on $ARCH"
echo ""
echo "💡 To view logs: docker compose -f $COMPOSE_FILE logs -f"
echo "🛑 To stop: docker compose -f $COMPOSE_FILE down"
