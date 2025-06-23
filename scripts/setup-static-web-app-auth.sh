#!/bin/bash

# Azure Static Web Apps Authentication Configuration Script
# Configures Entra External ID authentication for production deployment

set -e

echo "🔐 AZURE STATIC WEB APPS AUTHENTICATION SETUP"
echo "=============================================="
echo ""

# Configuration
RESOURCE_GROUP="sutra-rg"
STATIC_WEB_APP_NAME="sutra-web"
CLIENT_ID="61084964-08b8-49ea-b624-4859c4dc37de"
TENANT_DOMAIN="vedid.onmicrosoft.com"

# Color output functions
log_info() { echo -e "\033[36mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[32m✅ $1\033[0m"; }
log_warning() { echo -e "\033[33m⚠️  $1\033[0m"; }
log_error() { echo -e "\033[31m❌ $1\033[0m"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Configure Static Web App authentication
configure_static_web_app_auth() {
    log_info "Configuring Static Web App authentication..."

    # Check if Static Web App exists
    if ! az staticwebapp show --name "$STATIC_WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Static Web App '$STATIC_WEB_APP_NAME' not found in resource group '$RESOURCE_GROUP'"
        log_info "Please create the Static Web App first using:"
        echo "  az staticwebapp create --name $STATIC_WEB_APP_NAME --resource-group $RESOURCE_GROUP"
        exit 1
    fi

    # Get the Static Web App details
    static_app_url=$(az staticwebapp show \
        --name "$STATIC_WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        --output tsv)

    log_info "Static Web App URL: https://$static_app_url"

    # Configure environment variables
    log_info "Setting authentication environment variables..."

    # Set client ID (this is not sensitive)
    az staticwebapp appsettings set \
        --name "$STATIC_WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --setting-names "VED_EXTERNAL_ID_CLIENT_ID=$CLIENT_ID" \
        --output none

    log_success "Client ID configured"

    # Prompt for client secret
    echo ""
    log_warning "Client secret setup required:"
    echo "1. Go to Azure Portal -> Azure AD -> App Registrations"
    echo "2. Find the app registration with Client ID: $CLIENT_ID"
    echo "3. Go to 'Certificates & secrets' -> 'Client secrets'"
    echo "4. Create a new secret or copy existing secret value"
    echo ""

    read -p "Do you have the client secret ready? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -s -p "Enter the client secret: " client_secret
        echo ""

        if [[ -n "$client_secret" ]]; then
            az staticwebapp appsettings set \
                --name "$STATIC_WEB_APP_NAME" \
                --resource-group "$RESOURCE_GROUP" \
                --setting-names "VED_EXTERNAL_ID_CLIENT_SECRET=$client_secret" \
                --output none

            log_success "Client secret configured"
        else
            log_warning "Client secret not provided. You'll need to set it manually."
        fi
    else
        log_warning "Client secret not configured. Please set it manually in Azure Portal."
    fi
}

# Validate authentication configuration
validate_authentication() {
    log_info "Validating authentication configuration..."

    # Get the Static Web App URL
    static_app_url=$(az staticwebapp show \
        --name "$STATIC_WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        --output tsv)

    # Test authentication endpoints
    log_info "Testing authentication endpoints..."

    auth_me_url="https://$static_app_url/.auth/me"
    auth_providers_url="https://$static_app_url/.auth/providers"

    # Test /.auth/me endpoint
    if curl -s -o /dev/null -w "%{http_code}" "$auth_me_url" | grep -q "200\|401"; then
        log_success "/.auth/me endpoint is accessible"
    else
        log_warning "/.auth/me endpoint may not be properly configured"
    fi

    # Test /.auth/providers endpoint
    if curl -s -o /dev/null -w "%{http_code}" "$auth_providers_url" | grep -q "200"; then
        log_success "/.auth/providers endpoint is accessible"
    else
        log_warning "/.auth/providers endpoint may not be properly configured"
    fi
}

# Configure App Registration redirect URIs
configure_app_registration() {
    log_info "App Registration redirect URI configuration..."

    # Get the Static Web App URL
    static_app_url=$(az staticwebapp show \
        --name "$STATIC_WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        --output tsv)

    redirect_uri="https://$static_app_url/.auth/login/azureActiveDirectory/callback"

    echo ""
    log_info "Required App Registration configuration:"
    echo "🔧 App Registration Client ID: $CLIENT_ID"
    echo "🔧 Redirect URI: $redirect_uri"
    echo "🔧 Logout URL: https://$static_app_url/.auth/logout"
    echo ""

    log_warning "Manual steps required in Azure Portal:"
    echo "1. Go to Azure AD -> App Registrations -> $CLIENT_ID"
    echo "2. Click 'Authentication' in left menu"
    echo "3. Add Web platform if not already added"
    echo "4. Add redirect URI: $redirect_uri"
    echo "5. Add logout URL: https://$static_app_url/.auth/logout"
    echo "6. Enable 'ID tokens' under 'Implicit grant and hybrid flows'"
    echo "7. Save the configuration"
}

# Main execution
main() {
    echo "This script will configure Azure Static Web Apps authentication"
    echo "with Microsoft Entra External ID for the Sutra application."
    echo ""

    check_prerequisites
    configure_static_web_app_auth
    validate_authentication
    configure_app_registration

    echo ""
    log_success "Authentication configuration completed!"
    echo ""
    log_info "Next steps:"
    echo "1. Complete the manual App Registration configuration"
    echo "2. Test authentication by visiting your Static Web App"
    echo "3. Check the /.auth/me endpoint after login"
    echo "4. Verify that roles are correctly assigned via /api/getroles"
    echo ""
    log_info "Static Web App URL: https://$static_app_url"
    log_info "Test authentication: https://$static_app_url/.auth/login/azureActiveDirectory"
}

# Run main function
main "$@"
