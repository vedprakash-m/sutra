#!/bin/bash

# Azure App Registration Configuration for Sutra Production Deployment
# Configures Microsoft Entra ID for vedid.onmicrosoft.com tenant

set -euo pipefail

# Configuration
TENANT_DOMAIN="vedid.onmicrosoft.com"
APP_NAME="sutra-prod"
RESOURCE_GROUP="sutra-rg"
LOCATION="eastus2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Configuring Azure App Registration for Sutra Production${NC}"
echo "Tenant: ${TENANT_DOMAIN}"
echo "App Name: ${APP_NAME}"
echo "Resource Group: ${RESOURCE_GROUP}"
echo ""

# Function to check if Azure CLI is logged in
check_azure_login() {
    if ! az account show &>/dev/null; then
        echo -e "${RED}❌ Please login to Azure CLI first: az login${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Azure CLI authenticated${NC}"
}

# Function to get tenant ID
get_tenant_id() {
    TENANT_ID=$(az account show --query "tenantId" --output tsv)
    echo "Tenant ID: ${TENANT_ID}"
}

# Function to create app registration
create_app_registration() {
    echo -e "${YELLOW}📝 Creating app registration...${NC}"

    # Get resource group details
    RESOURCE_GROUP_INFO=$(az group show --name ${RESOURCE_GROUP} --query "{location:location,id:id}" --output json)
    RG_LOCATION=$(echo $RESOURCE_GROUP_INFO | jq -r '.location')

    # Get Static Web App URL
    STATIC_WEB_APP_NAME=$(az staticwebapp list --resource-group ${RESOURCE_GROUP} --query "[0].name" --output tsv)
    STATIC_WEB_APP_URL="https://$(az staticwebapp show --name ${STATIC_WEB_APP_NAME} --resource-group ${RESOURCE_GROUP} --query "defaultHostname" --output tsv)"

    echo "Static Web App URL: ${STATIC_WEB_APP_URL}"

    # Create app registration
    APP_REGISTRATION=$(az ad app create \
        --display-name "${APP_NAME}" \
        --identifier-uris "api://${APP_NAME}" \
        --web-redirect-uris "${STATIC_WEB_APP_URL}/.auth/login/aad/callback" \
        --web-home-page-url "${STATIC_WEB_APP_URL}" \
        --sign-in-audience "AzureADMyOrg" \
        --required-resource-accesses '[
            {
                "resourceAppId": "00000003-0000-0000-c000-000000000000",
                "resourceAccess": [
                    {
                        "id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d",
                        "type": "Scope"
                    },
                    {
                        "id": "37f7f235-527c-4136-accd-4a02d197296e",
                        "type": "Scope"
                    }
                ]
            }
        ]' \
        --output json)

    APP_ID=$(echo $APP_REGISTRATION | jq -r '.appId')
    OBJECT_ID=$(echo $APP_REGISTRATION | jq -r '.id')

    echo -e "${GREEN}✅ App registration created${NC}"
    echo "App ID (Client ID): ${APP_ID}"
    echo "Object ID: ${OBJECT_ID}"

    # Create service principal
    echo -e "${YELLOW}📝 Creating service principal...${NC}"
    SP_RESULT=$(az ad sp create --id ${APP_ID} --output json)
    SP_OBJECT_ID=$(echo $SP_RESULT | jq -r '.id')

    echo -e "${GREEN}✅ Service principal created${NC}"
    echo "Service Principal Object ID: ${SP_OBJECT_ID}"

    # Generate client secret
    echo -e "${YELLOW}🔐 Generating client secret...${NC}"
    CLIENT_SECRET_RESULT=$(az ad app credential reset --id ${APP_ID} --display-name "sutra-prod-secret" --output json)
    CLIENT_SECRET=$(echo $CLIENT_SECRET_RESULT | jq -r '.password')

    echo -e "${GREEN}✅ Client secret generated${NC}"
    echo -e "${YELLOW}⚠️  Save this client secret securely - it won't be shown again!${NC}"

    # Store in environment variables file
    ENV_FILE="./production.env"
    cat > ${ENV_FILE} << EOF
# Production Environment Variables for Sutra
# Generated on $(date)

# Microsoft Entra ID Configuration
VITE_ENTRA_CLIENT_ID=${APP_ID}
VITE_ENTRA_TENANT_ID=${TENANT_ID}
VITE_ENTRA_REDIRECT_URI=${STATIC_WEB_APP_URL}

# Azure Static Web Apps Configuration
VED_EXTERNAL_ID_CLIENT_ID=${APP_ID}
VED_EXTERNAL_ID_CLIENT_SECRET=${CLIENT_SECRET}

# Production API Configuration
VITE_API_BASE_URL=https://$(az functionapp list --resource-group ${RESOURCE_GROUP} --query "[0].defaultHostName" --output tsv)/api
VITE_USE_LOCAL_API=false
VITE_ENABLE_GUEST_MODE=true
VITE_ENABLE_MOCK_AUTH=false

# Analytics and Monitoring
VITE_ENABLE_ANALYTICS=true
VITE_APPLICATION_INSIGHTS_KEY=$(az monitor app-insights component show --app sutra-ai --resource-group ${RESOURCE_GROUP} --query "instrumentationKey" --output tsv)

# Environment Settings
NODE_ENV=production
EOF

    echo -e "${GREEN}✅ Environment variables saved to ${ENV_FILE}${NC}"

    # Output summary
    echo ""
    echo -e "${GREEN}🎉 Azure App Registration Configuration Complete!${NC}"
    echo ""
    echo "Summary:"
    echo "  - App Registration: ${APP_NAME}"
    echo "  - Client ID: ${APP_ID}"
    echo "  - Tenant ID: ${TENANT_ID}"
    echo "  - Redirect URI: ${STATIC_WEB_APP_URL}/.auth/login/aad/callback"
    echo "  - Environment file: ${ENV_FILE}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Review the generated ${ENV_FILE} file"
    echo "2. Run: ./scripts/deploy-production-config.sh"
    echo "3. Test authentication flow"
    echo ""
    echo -e "${RED}⚠️  Important: Store the client secret securely!${NC}"
}

# Main execution
main() {
    check_azure_login
    get_tenant_id
    create_app_registration
}

main "$@"
