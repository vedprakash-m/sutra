#!/bin/bash

# Sutra Infrastructure Verification Script
# Validates the unified infrastructure deployment

echo "🔍 Sutra Infrastructure Verification Script"
echo "============================================="

# Check Azure CLI login
echo "✅ Checking Azure CLI authentication..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Azure CLI not authenticated. Please run 'az login'"
    exit 1
fi

echo "✅ Azure CLI authenticated: $(az account show --query name -o tsv)"

# Check resource group
echo "✅ Checking unified resource group..."
if ! az group show --name sutra-rg > /dev/null 2>&1; then
    echo "❌ Resource group 'sutra-rg' not found"
    exit 1
fi

echo "✅ Resource group 'sutra-rg' exists"

# Validate unified template
echo "🔍 Validating unified Bicep template..."
if az deployment group validate \
    --resource-group sutra-rg \
    --template-file infrastructure/unified.bicep \
    --parameters @infrastructure/parameters.unified.json > /dev/null 2>&1; then
    echo "✅ Unified template validation passed"
else
    echo "❌ Template validation failed"
    exit 1
fi

# Check if resources exist (for existing deployments)
echo "🔍 Checking existing resources..."

# Check Cosmos DB
if az cosmosdb show --name sutra-db --resource-group sutra-rg > /dev/null 2>&1; then
    echo "✅ Cosmos DB (sutra-db) exists"
else
    echo "⚠️  Cosmos DB not deployed yet"
fi

# Check Function App with Flex Consumption
FUNCTION_APPS=$(az functionapp list --resource-group sutra-rg --query "[].name" -o tsv)
if [ ! -z "$FUNCTION_APPS" ]; then
    for app in $FUNCTION_APPS; do
        PLAN_ID=$(az functionapp show --name $app --resource-group sutra-rg --query "serverFarmId" -o tsv)
        PLAN_NAME=$(basename $PLAN_ID)
        SKU=$(az appservice plan show --ids $PLAN_ID --query "sku.name" -o tsv)
        echo "✅ Function App: $app (Plan: $PLAN_NAME, SKU: $SKU)"
    done
else
    echo "⚠️  Function Apps not deployed yet"
fi

# Check Static Web App
STATIC_APPS=$(az staticwebapp list --resource-group sutra-rg --query "[].name" -o tsv)
if [ ! -z "$STATIC_APPS" ]; then
    for app in $STATIC_APPS; do
        echo "✅ Static Web App: $app"
    done
else
    echo "⚠️  Static Web Apps not deployed yet"
fi

# Check Key Vault
KEY_VAULTS=$(az keyvault list --resource-group sutra-rg --query "[].name" -o tsv)
if [ ! -z "$KEY_VAULTS" ]; then
    for vault in $KEY_VAULTS; do
        echo "✅ Key Vault: $vault"
    done
else
    echo "⚠️  Key Vault not deployed yet"
fi

echo ""
echo "🎯 Infrastructure Status Summary:"
echo "================================="
echo "✅ Unified Resource Group: Ready"
echo "✅ Bicep Template: Validated"
echo "✅ Azure CLI: Configured"
echo "✅ Deployment: Ready to execute"
echo ""
echo "🚀 To deploy, run:"
echo "az deployment group create --resource-group sutra-rg --template-file infrastructure/unified.bicep --parameters @infrastructure/parameters.unified.json"
