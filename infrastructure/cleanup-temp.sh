#!/bin/bash

# Cleanup script to remove temporary resources after idempotent deployment
# Only run this AFTER successfully deploying idempotent.bicep

set -e

RESOURCE_GROUP="sutra-rg"

echo "🧹 Starting cleanup of temporary resources..."

# Function to safely delete a resource
delete_resource() {
    local resource_name=$1
    local resource_type=$2

    echo "🗑️  Checking for $resource_name ($resource_type)..."

    if az resource show --resource-group $RESOURCE_GROUP --name $resource_name --resource-type $resource_type &>/dev/null; then
        echo "   Found $resource_name, deleting..."
        az resource delete --resource-group $RESOURCE_GROUP --name $resource_name --resource-type $resource_type --verbose
        echo "   ✅ Deleted $resource_name"
    else
        echo "   ⏭️  $resource_name not found or already deleted"
    fi
}

# Clean up temporary Flex Function App (if still exists)
delete_resource "sutra-flex-api-hvyqgbrvnx4ii" "Microsoft.Web/sites"

# Clean up temporary Flex App Service Plan (if still exists)
delete_resource "sutra-flex-plan" "Microsoft.Web/serverfarms"

# Clean up old Static Web App with hash suffix
delete_resource "sutra-web-hvyqgbrvnx4ii" "Microsoft.Web/staticSites"

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📊 Final Infrastructure Summary:"
az resource list --resource-group $RESOURCE_GROUP --output table | grep -E "(sutra-|cosmos)"

echo ""
echo "🎯 Your infrastructure is now fully consolidated with idempotent naming:"
echo "  • sutra-kv (Key Vault)"
echo "  • sutrasa99 (Storage Account)"
echo "  • sutra-api (Function App)"
echo "  • sutra-plan (App Service Plan)"
echo "  • sutra-web (Static Web App)"
echo "  • sutra-db (Cosmos DB)"
echo "  • sutra-logs (Log Analytics)"
echo "  • sutra-ai (Application Insights)"
echo ""
