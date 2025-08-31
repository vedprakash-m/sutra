#!/bin/bash

# Idempotent Infrastructure Deployment
# Safely deploys Sutra infrastructure with static naming
# This script handles the transition from temporary to permanent naming

set -e

RESOURCE_GROUP="sutra-rg"
LOCATION="eastus"
TEMPLATE_FILE="idempotent.bicep"

echo "🚀 Starting idempotent infrastructure deployment..."

# Validate template
echo "📋 Validating Bicep template..."
az deployment group validate \
  --resource-group $RESOURCE_GROUP \
  --template-file $TEMPLATE_FILE \
  --parameters location=$LOCATION

# Preview what would be deployed
echo "👀 Previewing deployment changes..."
az deployment group what-if \
  --resource-group $RESOURCE_GROUP \
  --template-file $TEMPLATE_FILE \
  --parameters location=$LOCATION

# Ask for confirmation
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

# Deploy the template
echo "🎯 Deploying idempotent infrastructure..."
DEPLOYMENT_NAME="sutra-idempotent-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file $TEMPLATE_FILE \
  --parameters location=$LOCATION \
  --name $DEPLOYMENT_NAME \
  --verbose

# Get deployment outputs
echo "📋 Getting deployment outputs..."
FUNCTION_APP_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name $DEPLOYMENT_NAME \
  --query 'properties.outputs.functionAppUrl.value' \
  --output tsv)

API_BASE_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name $DEPLOYMENT_NAME \
  --query 'properties.outputs.apiBaseUrl.value' \
  --output tsv)

STATIC_WEB_APP_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name $DEPLOYMENT_NAME \
  --query 'properties.outputs.staticWebAppUrl.value' \
  --output tsv)

echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Deployment Summary:"
echo "  • Function App: $FUNCTION_APP_URL"
echo "  • API Base URL: $API_BASE_URL"
echo "  • Static Web App: $STATIC_WEB_APP_URL"
echo ""
echo "🔄 Next steps:"
echo "  1. Update frontend configuration to use new endpoints"
echo "  2. Deploy frontend to new Static Web App"
echo "  3. Clean up temporary resources"
echo ""
