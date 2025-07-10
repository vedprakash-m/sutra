#!/bin/bash

# Build Bicep Infrastructure Templates
# This script builds .bicep files into .json ARM templates
# Use this when you need to generate/update ARM templates for deployment

set -e

echo "🏗️  Building Bicep templates to ARM JSON..."

# Check if Azure CLI is available
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install Azure CLI first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Install/update Bicep CLI
echo "📦 Ensuring Bicep CLI is up to date..."
az bicep install >/dev/null 2>&1

# Change to infrastructure directory
cd "$(dirname "$0")/../infrastructure"

# Build each Bicep file
for bicep_file in *.bicep; do
    if [ -f "$bicep_file" ] && [ -s "$bicep_file" ]; then
        json_file="${bicep_file%.bicep}.json"
        echo "🔨 Building $bicep_file -> $json_file"
        az bicep build --file "$bicep_file" --outfile "$json_file"
    fi
done

echo "✅ Bicep templates built successfully!"
echo ""
echo "📋 Generated ARM templates:"
ls -la *.json | grep -v parameters

echo ""
echo "💡 Remember to commit the updated JSON files if they've changed:"
echo "   git add infrastructure/*.json"
echo "   git commit -m 'build: update ARM templates from Bicep changes'"
