#!/bin/bash

# E2E Cleanup Script - Compatible with both local and CI/CD environments
# This script handles Docker Compose differences between environments

set -e

echo "🧹 Cleaning up E2E services..."

# Function to run docker compose with fallback
run_docker_compose() {
    local cmd="$1"

    # Try modern docker compose first (preferred in CI/CD)
    if docker compose version >/dev/null 2>&1; then
        echo "Using 'docker compose' (modern)"
        docker compose $cmd
    # Fall back to legacy docker-compose
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "Using 'docker-compose' (legacy)"
        docker-compose $cmd
    else
        echo "❌ Neither 'docker compose' nor 'docker-compose' is available"
        echo "Please install Docker Compose"
        exit 1
    fi
}

# Stop and remove services
run_docker_compose "down"

# Restore original configuration
echo "🔧 Restoring original configuration..."
if [ -f "api/local.settings.json.backup" ]; then
    mv api/local.settings.json.backup api/local.settings.json
    echo "✅ Original configuration restored"
else
    echo "ℹ️  No backup found, keeping current configuration"
fi

echo "✅ E2E services cleaned up successfully"
