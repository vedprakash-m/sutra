#!/bin/bash

# Simple test script to check our Docker validation logic

echo "🧪 Testing Docker build validation..."

# Test the validation logic for the specific issue
build_script=$(grep '"build":' package.json | sed 's/.*"build": "\([^"]*\)".*/\1/')
echo "Build script: $build_script"

if echo "$build_script" | grep -q "tsc"; then
    echo "✅ Build script uses tsc"        # Check if typescript is in devDependencies
        if grep -A30 '"devDependencies"' package.json | grep -q '"typescript"'; then
        echo "✅ TypeScript found in devDependencies"

        # Check Dockerfile for problematic pattern
        if grep -q "npm ci --only=production" Dockerfile.e2e; then
            echo "❌ VALIDATION FAILED: Dockerfile.e2e uses --only=production but build requires devDependencies (like tsc)"
            echo "❌ This will cause 'tsc: not found' errors in CI/CD"
            exit 1
        else
            echo "✅ Dockerfile.e2e correctly installs all dependencies"
        fi
    else
        echo "❌ TypeScript not found in devDependencies but required by build script"
        exit 1
    fi
else
    echo "❌ Build script does not use tsc"
fi

echo "✅ Docker build validation passed"
