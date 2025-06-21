#!/bin/bash

# Simple E2E test to catch container issues locally
# This mirrors the CI/CD E2E setup exactly

set -e

echo "🐳 LOCAL E2E CONTAINER TEST"
echo "==========================="
echo ""

# Check Docker availability
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running - start Docker Desktop first"
    exit 1
fi

echo "✅ Docker is available"

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down -v 2>/dev/null || true
docker system prune -f >/dev/null 2>&1 || true

# Build containers (matching CI exactly)
echo "🏗️  Building containers..."
if ! docker-compose build --no-cache; then
    echo "❌ Container build failed"
    exit 1
fi

echo "✅ Containers built successfully"

# Start containers and capture logs
echo "🚀 Starting containers..."
docker-compose up -d

# Wait a moment for startup
sleep 5

# Check container status
echo "📊 Container status:"
docker-compose ps

# Get logs from functions-api to see why it's failing
echo ""
echo "📋 Functions API container logs:"
echo "================================"
docker-compose logs functions-api

# Check if containers are actually running
if docker-compose ps | grep -q "Exit 1"; then
    echo ""
    echo "❌ Container exited with error - this will fail CI/CD"
    echo ""
    echo "All container logs:"
    docker-compose logs
    docker-compose down -v
    exit 1
fi

echo ""
echo "✅ E2E container test passed!"

# Cleanup
docker-compose down -v

echo "🎉 Ready for CI/CD deployment!"
