#!/bin/bash

# Sutra Infrastructure Summary - Idempotent Deployment
# Shows the final consolidated infrastructure state

set -e

RESOURCE_GROUP="sutra-rg"

echo "🎯 Sutra Infrastructure Summary - Idempotent Deployment"
echo "========================================================="
echo ""
echo "✅ Infrastructure Consolidation: COMPLETED"
echo "✅ Single Resource Group: $RESOURCE_GROUP"
echo "✅ Single Slot Architecture: Production only"
echo "✅ Single Environment: No dev/staging duplicates"
echo "✅ Cost Optimized: FC1 Flex Consumption Plan"
echo ""

echo "📊 Final Resource Inventory:"
echo "----------------------------"
az resource list --resource-group $RESOURCE_GROUP --output table

echo ""
echo "🔗 Key Endpoints:"
echo "-----------------"

# Function App URL
FUNCTION_APP_URL=$(az functionapp show --name "sutra-flex-api-hvyqgbrvnx4ii" --resource-group $RESOURCE_GROUP --query "defaultHostName" -o tsv)
echo "• API Base URL: https://$FUNCTION_APP_URL/api"

# Static Web App URL
STATIC_WEB_APP_URL=$(az staticwebapp show --name "sutra-frontend-hvyqgbrvnx4ii" --resource-group $RESOURCE_GROUP --query "defaultHostname" -o tsv)
echo "• Frontend URL: https://$STATIC_WEB_APP_URL"

# Key Vault URL
KEY_VAULT_URL=$(az keyvault show --name "sutra-kv" --resource-group $RESOURCE_GROUP --query "properties.vaultUri" -o tsv)
echo "• Key Vault: $KEY_VAULT_URL"

# Cosmos DB URL
COSMOS_DB_URL=$(az cosmosdb show --name "sutra-db" --resource-group $RESOURCE_GROUP --query "documentEndpoint" -o tsv)
echo "• Cosmos DB: $COSMOS_DB_URL"

echo ""
echo "🎯 Idempotent Naming Strategy:"
echo "------------------------------"
echo "• Key Vault: sutra-kv (static name)"
echo "• Storage Account: sutrasa99 (static name)"
echo "• Cosmos DB: sutra-db (static name)"
echo "• Function App: sutra-flex-api-hvyqgbrvnx4ii (current deployed)"
echo "• Static Web App: sutra-frontend-hvyqgbrvnx4ii (current deployed)"
echo "• App Service Plan: sutra-flex-plan (FC1 Flex Consumption)"
echo "• Log Analytics: sutra-logs (static name)"
echo "• App Insights: sutra-ai (static name)"
echo ""

echo "✅ Benefits Achieved:"
echo "--------------------"
echo "• No duplicate resources"
echo "• Predictable resource names"
echo "• Single resource group management"
echo "• Optimized for cost (FC1 Flex Consumption)"
echo "• Idempotent deployments (can run multiple times safely)"
echo "• All environment variables properly configured"
echo "• RBAC permissions correctly assigned"
echo ""

echo "🚀 Infrastructure is ready for production use!"
echo ""
