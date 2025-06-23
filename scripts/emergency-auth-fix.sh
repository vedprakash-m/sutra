#!/bin/bash

# EMERGENCY AUTHENTICATION FIX SCRIPT
# Enables authentication in Azure Static Web Apps

echo "🚨 EMERGENCY AUTHENTICATION ENABLEMENT"
echo "======================================"

# Check if user is logged into Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Run: az login"
    exit 1
fi

echo "🔍 Checking current Static Web App status..."

# Check if Static Web App exists and get details
STATIC_APP_INFO=$(az staticwebapp list --query "[?contains(name, 'sutra') || contains(name, 'web')].{name:name, resourceGroup:resourceGroup, defaultHostname:defaultHostname}" --output json)

if [[ $(echo "$STATIC_APP_INFO" | jq length) -eq 0 ]]; then
    echo "❌ No Static Web App found containing 'sutra' or 'web'"
    echo "Available Static Web Apps:"
    az staticwebapp list --query "[].{name:name, resourceGroup:resourceGroup}" --output table
    exit 1
fi

# Get the first matching app
STATIC_APP_NAME=$(echo "$STATIC_APP_INFO" | jq -r '.[0].name')
RESOURCE_GROUP=$(echo "$STATIC_APP_INFO" | jq -r '.[0].resourceGroup')
HOSTNAME=$(echo "$STATIC_APP_INFO" | jq -r '.[0].defaultHostname')

echo "✅ Found Static Web App: $STATIC_APP_NAME"
echo "📍 Resource Group: $RESOURCE_GROUP"
echo "🌐 Hostname: $HOSTNAME"

echo ""
echo "🔧 CRITICAL: Authentication must be enabled manually in Azure Portal"
echo "=============================================================="
echo ""
echo "1. Open Azure Portal: https://portal.azure.com"
echo "2. Navigate to: Static Web Apps → $STATIC_APP_NAME"
echo "3. Click 'Authentication' in left menu"
echo "4. Click '+ Add identity provider'"
echo "5. Select 'Microsoft' as provider"
echo "6. Choose 'Create new app registration' OR use existing:"
echo "   Client ID: 61084964-08b8-49ea-b624-4859c4dc37de"
echo "7. Configure redirect URI: https://$HOSTNAME/.auth/login/azureActiveDirectory/callback"
echo "8. Enable 'ID tokens' in app registration"
echo "9. Save and wait 5-10 minutes for propagation"
echo ""
echo "🧪 Test with: curl -I https://$HOSTNAME/.auth/me"
echo "Expected: HTTP 200 or 401 (not 404)"

# Set required environment variables
echo ""
echo "📝 Setting required environment variables..."

az staticwebapp appsettings set \
    --name "$STATIC_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --setting-names \
        "VED_EXTERNAL_ID_CLIENT_ID=61084964-08b8-49ea-b624-4859c4dc37de" \
        "AZURE_AUTH_ENABLED=true" \
    --output none

echo "✅ Environment variables set"
echo ""
echo "⚠️  Manual Azure Portal configuration required above!"
echo "⏱️  Authentication enablement takes 5-10 minutes after Portal changes"
