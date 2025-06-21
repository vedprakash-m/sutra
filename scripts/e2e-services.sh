#!/bin/bash

# E2E Services Status Script - Compatible with both local and CI/CD environments

set -e

# Function to run docker compose with fallback
run_docker_compose() {
    local cmd="$1"

    # Try modern docker compose first (preferred in CI/CD)
    if docker compose version >/dev/null 2>&1; then
        docker compose $cmd
    # Fall back to legacy docker-compose
    elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose $cmd
    else
        echo "❌ Neither 'docker compose' nor 'docker-compose' is available"
        exit 1
    fi
}

# Show service status
run_docker_compose "ps"
