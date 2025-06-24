#!/bin/bash

# Fix Authentication Configuration Script
# This script helps diagnose and fix Microsoft Entra External ID authentication issues

echo "🔧 AUTHENTICATION CONFIGURATION FIX"
echo "====================================="
echo

# Configuration variables
RESOURCE_GROUP="sutra-rg"
STATIC_WEB_APP_NAME="sutra-web-hvyqgbrvnx4ii"
CLIENT_ID="713d0c7d-e0fb-4390-95e2-42019b52a656"
TENANT_DOMAIN="vedid.onmicrosoft.com"

echo "📋 Current Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Static Web App: $STATIC_WEB_APP_NAME"
echo "  Client ID: $CLIENT_ID"
echo "  Tenant Domain: $TENANT_DOMAIN"
echo

# Step 1: Check if Azure CLI is logged in
echo "🔐 Step 1: Checking Azure CLI Authentication"
echo "--------------------------------------------"
if ! az account show &>/dev/null; then
    echo "❌ Azure CLI not logged in. Please run: az login"
    exit 1
fi
echo "✅ Azure CLI authenticated"
echo

# Step 2: Check if Static Web App exists
echo "🌐 Step 2: Checking Static Web App Existence"
echo "-------------------------------------------"
if ! az staticwebapp show --name "$STATIC_WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "❌ Static Web App '$STATIC_WEB_APP_NAME' not found in resource group '$RESOURCE_GROUP'"
    echo "📝 Available Static Web Apps:"
    az staticwebapp list --resource-group "$RESOURCE_GROUP" --query "[].name" -o table 2>/dev/null || echo "  No Static Web Apps found"
    exit 1
fi
echo "✅ Static Web App found"
echo

# Step 3: Check current app settings
echo "⚙️  Step 3: Checking Current App Settings"
echo "-----------------------------------------"
echo "Current environment variables:"
az staticwebapp appsettings list --name "$STATIC_WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties" -o table 2>/dev/null || echo "  Failed to retrieve app settings"
echo

# Step 4: Set required environment variables
echo "🔧 Step 4: Setting Required Environment Variables"
echo "------------------------------------------------"

# Check if client secret is available (it should come from Key Vault or be provided)
if [ -z "$VED_EXTERNAL_ID_CLIENT_SECRET" ]; then
    echo "⚠️  VED_EXTERNAL_ID_CLIENT_SECRET not provided"
    echo "📝 You need to provide the client secret. Get it from:"
    echo "   1. Azure Portal > App Registrations > Sutra External ID > Certificates & secrets"
    echo "   2. Or from Azure Key Vault if stored there"
    echo
    echo "To set the secret, run:"
    echo "  export VED_EXTERNAL_ID_CLIENT_SECRET='your-secret-here'"
    echo "  $0"
    echo
    exit 1
fi

echo "Setting VED_EXTERNAL_ID_CLIENT_ID..."
az staticwebapp appsettings set \
    --name "$STATIC_WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --setting-names "VED_EXTERNAL_ID_CLIENT_ID=$CLIENT_ID" \
    --output none

echo "Setting VED_EXTERNAL_ID_CLIENT_SECRET..."
az staticwebapp appsettings set \
    --name "$STATIC_WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --setting-names "VED_EXTERNAL_ID_CLIENT_SECRET=$VED_EXTERNAL_ID_CLIENT_SECRET" \
    --output none

echo "✅ Environment variables set"
echo

# Step 5: Verify configuration
echo "✅ Step 5: Verifying Configuration"
echo "----------------------------------"
echo "Updated environment variables:"
az staticwebapp appsettings list --name "$STATIC_WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties" -o table
echo

# Step 6: Check app registration configuration
echo "🔍 Step 6: App Registration Checklist"
echo "------------------------------------"
echo "Please verify the following in Azure Portal:"
echo
echo "1. 📱 App Registration (https://portal.azure.com > App registrations):"
echo "   - Name: Sutra External ID"
echo "   - Application ID: $CLIENT_ID"
echo "   - Supported account types: Any identity provider or organizational directory (for authenticating users with user flows)"
echo
echo "2. 🔗 Redirect URIs:"
echo "   - Web platform should include:"
echo "     • https://sutra-static-web-app.azurestaticapps.net/.auth/login/azureActiveDirectory/callback"
echo "     • https://sutra-static-web-app.azurestaticapps.net/.auth/login/aad/callback"
echo
echo "3. 🎟️  Authentication > Token configuration:"
echo "   - ID tokens checkbox should be CHECKED"
echo "   - Access tokens can be unchecked"
echo
echo "4. 🔐 Certificates & secrets:"
echo "   - Should have a valid client secret"
echo "   - Secret should not be expired"
echo

# Step 7: Test authentication
echo "🧪 Step 7: Testing Authentication"
echo "--------------------------------"
STATIC_WEB_APP_URL=$(az staticwebapp show --name "$STATIC_WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "defaultHostname" -o tsv)
if [ -n "$STATIC_WEB_APP_URL" ]; then
    echo "🌐 Static Web App URL: https://$STATIC_WEB_APP_URL"
    echo "🔗 Test authentication: https://$STATIC_WEB_APP_URL/.auth/login/azureActiveDirectory"
    echo "📋 User info endpoint: https://$STATIC_WEB_APP_URL/.auth/me"
    echo
    echo "✅ Configuration complete!"
    echo
    echo "🔄 Note: Changes may take 2-3 minutes to take effect."
    echo "🌐 Try signing in at: https://$STATIC_WEB_APP_URL"
else
    echo "❌ Could not retrieve Static Web App URL"
fi

echo
echo "🚨 TROUBLESHOOTING"
echo "=================="
echo "If authentication still fails:"
echo "1. Wait 2-3 minutes for configuration to propagate"
echo "2. Clear browser cache and cookies"
echo "3. Try incognito/private browsing mode"
echo "4. Check browser developer console for errors"
echo "5. Verify all redirect URIs in App Registration"
echo
