#!/bin/bash

# No-Gateway Deployment Script for Sutra
# Deploys Azure Functions directly without API Management Gateway
# Architecture: Static Web App + Azure Functions (Direct Access)

set -e

echo "🚀 Sutra No-Gateway Deployment"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DEPLOYMENT_ID=$(date +%Y%m%d-%H%M%S)
RESOURCE_GROUP="sutra-rg"
LOCATION="eastus"

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not installed"
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure CLI. Run: az login"
    fi

    # Check required files
    if [ ! -f "infrastructure/compute-no-gateway.bicep" ]; then
        log_error "No-gateway Bicep template not found"
    fi

    if [ ! -f "infrastructure/parameters.compute-no-gateway.json" ]; then
        log_error "No-gateway parameters file not found"
    fi

    # Validate templates
    if ! az bicep build --file infrastructure/compute-no-gateway.bicep --stdout > /dev/null; then
        log_error "No-gateway Bicep template validation failed"
    fi

    log_success "Prerequisites check passed"
}

# Ensure resource group exists
ensure_resource_group() {
    log_info "Ensuring resource group exists..."

    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Resource group '$RESOURCE_GROUP' exists"
    else
        log_info "Creating resource group '$RESOURCE_GROUP'..."
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        log_success "Resource group created"
    fi
}

# Deploy persistent infrastructure if needed
deploy_persistent_infrastructure() {
    log_info "Checking persistent infrastructure..."

    # Check if key vault exists (indicator of persistent infrastructure)
    local key_vault_name="sutra-kv-$(az account show --query id -o tsv | cut -c1-8)"

    if az keyvault show --name "$key_vault_name" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Persistent infrastructure already exists"
    else
        log_info "Deploying persistent infrastructure first..."

        # Deploy persistent infrastructure
        az deployment group create \
            --resource-group "$RESOURCE_GROUP" \
            --template-file infrastructure/persistent.bicep \
            --parameters @infrastructure/parameters.persistent.json \
            --name "persistent-$DEPLOYMENT_ID"

        log_success "Persistent infrastructure deployed"
    fi
}

# Get persistent infrastructure outputs
get_persistent_outputs() {
    log_info "Retrieving persistent infrastructure outputs..."

    # Get the latest successful persistent deployment
    local deployment_name=$(az deployment group list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?contains(name, 'persistent') && properties.provisioningState=='Succeeded'] | sort_by(@, &properties.timestamp) | [-1].name" \
        -o tsv)

    if [ -z "$deployment_name" ]; then
        log_error "No successful persistent deployment found"
    fi

    # Extract outputs
    COSMOS_CONNECTION_STRING=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$deployment_name" \
        --query "properties.outputs.cosmosDbConnectionString.value" \
        -o tsv)

    STORAGE_CONNECTION_STRING=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$deployment_name" \
        --query "properties.outputs.storageConnectionString.value" \
        -o tsv)

    KEY_VAULT_URI=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$deployment_name" \
        --query "properties.outputs.keyVaultUri.value" \
        -o tsv)

    log_success "Retrieved persistent infrastructure outputs"
}

# Deploy no-gateway compute infrastructure
deploy_compute_infrastructure() {
    log_info "Deploying no-gateway compute infrastructure..."

    # Deploy compute infrastructure with no-gateway template
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infrastructure/compute-no-gateway.bicep \
        --parameters @infrastructure/parameters.compute-no-gateway.json \
        --parameters cosmosDbConnectionString="$COSMOS_CONNECTION_STRING" \
        --parameters storageConnectionString="$STORAGE_CONNECTION_STRING" \
        --parameters keyVaultUri="$KEY_VAULT_URI" \
        --name "compute-no-gateway-$DEPLOYMENT_ID" \
        --verbose

    log_success "No-gateway compute infrastructure deployed"
}

# Build and deploy Azure Functions
deploy_azure_functions() {
    log_info "Building and deploying Azure Functions..."

    # Get function app name
    local function_app_name="sutra-api"

    # Create deployment package
    cd api

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --target .python_packages/lib/site-packages
    fi

    # Create zip package
    zip -r ../function-app.zip . -x "*.pyc" "*/__pycache__/*" "tests/*" "*_test.py"
    cd ..

    # Deploy function app
    az functionapp deployment source config-zip \
        --resource-group "$RESOURCE_GROUP" \
        --name "$function_app_name" \
        --src function-app.zip

    # Clean up
    rm -f function-app.zip

    log_success "Azure Functions deployed"
}

# Build and deploy Static Web App
deploy_static_web_app() {
    log_info "Building and deploying Static Web App..."

    # Build frontend
    npm ci
    npm run build

    # Get Static Web App name
    local swa_name="sutra-web"

    # Check if Static Web App exists
    if ! az staticwebapp show --name "$swa_name" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_info "Creating Static Web App..."

        # Create Static Web App
        az staticwebapp create \
            --name "$swa_name" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --source https://github.com/vedprakash-m/sutra \
            --branch main \
            --app-location "/" \
            --api-location "api" \
            --output-location "dist"

        log_success "Static Web App created"
    else
        log_success "Static Web App already exists"
    fi

    # Deploy to Static Web App (if using Azure CLI deployment)
    if command -v swa &> /dev/null; then
        swa deploy ./dist --env production
        log_success "Static Web App deployed"
    else
        log_info "Static Web App will be deployed via GitHub Actions"
    fi
}

# Configure function app settings
configure_function_app() {
    log_info "Configuring Azure Functions app settings..."

    local function_app_name="sutra-api"

    # Set additional app settings for no-gateway architecture
    az functionapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$function_app_name" \
        --settings \
        "SUTRA_ARCHITECTURE=no-gateway" \
        "SUTRA_DEPLOYMENT_ID=$DEPLOYMENT_ID" \
        "SUTRA_API_VERSION=1.0"

    log_success "Function app settings configured"
}

# Update CORS settings for no-gateway
update_cors_settings() {
    log_info "Updating CORS settings for no-gateway architecture..."

    local function_app_name="sutra-api"

    # Get Static Web App URL
    local swa_url=$(az staticwebapp show \
        --name "sutra-web" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        -o tsv)

    if [ -n "$swa_url" ]; then
        # Update CORS to include Static Web App URL
        az functionapp cors add \
            --resource-group "$RESOURCE_GROUP" \
            --name "$function_app_name" \
            --allowed-origins "https://$swa_url"

        log_success "CORS settings updated for Static Web App"
    fi
}

# Validate deployment
validate_deployment() {
    log_info "Validating no-gateway deployment..."

    # Test function app health
    local function_app_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "sutra-api" \
        --query "defaultHostName" \
        -o tsv)

    if curl -f "https://$function_app_url/api/health" &> /dev/null; then
        log_success "Azure Functions health check passed"
    else
        log_warning "Azure Functions health check failed or not ready yet"
    fi

    # Test Static Web App
    local swa_url=$(az staticwebapp show \
        --name "sutra-web" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        -o tsv 2>/dev/null || echo "")

    if [ -n "$swa_url" ] && curl -f "https://$swa_url" &> /dev/null; then
        log_success "Static Web App health check passed"
    else
        log_warning "Static Web App not ready or health check failed"
    fi
}

# Display deployment summary
show_deployment_summary() {
    echo ""
    echo "🎉 No-Gateway Deployment Summary"
    echo "================================"
    echo ""

    # Function App URL
    local function_app_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "sutra-api" \
        --query "defaultHostName" \
        -o tsv)

    echo "🔗 API Endpoint: https://$function_app_url"

    # Static Web App URL
    local swa_url=$(az staticwebapp show \
        --name "sutra-web" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        -o tsv 2>/dev/null || echo "")

    if [ -n "$swa_url" ]; then
        echo "🌐 Web App: https://$swa_url"
    fi

    echo ""
    echo "✅ Deployment ID: $DEPLOYMENT_ID"
    echo "📊 Resource Group: $RESOURCE_GROUP"
    echo "🏗️  Architecture: No-Gateway (Direct Access)"
    echo ""
    echo "Next steps:"
    echo "1. Run validation: ./scripts/validate-no-gateway.sh"
    echo "2. Run E2E tests: npm run test:e2e"
    echo "3. Monitor logs: az functionapp logs tail --name sutra-api --resource-group $RESOURCE_GROUP"
}

# Main deployment flow
main() {
    local start_time=$(date +%s)

    echo "Starting no-gateway deployment..."
    echo "Deployment ID: $DEPLOYMENT_ID"
    echo ""

    check_prerequisites
    ensure_resource_group
    deploy_persistent_infrastructure
    get_persistent_outputs
    deploy_compute_infrastructure
    deploy_azure_functions
    deploy_static_web_app
    configure_function_app
    update_cors_settings
    validate_deployment

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    show_deployment_summary

    log_success "No-gateway deployment completed successfully in ${duration}s!"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --validate     Run validation only"
        echo ""
        echo "This script deploys Sutra using no-gateway architecture:"
        echo "- Azure Functions (direct access)"
        echo "- Static Web App"
        echo "- No API Management Gateway"
        exit 0
        ;;
    --validate)
        ./scripts/validate-no-gateway.sh
        exit $?
        ;;
    *)
        main "$@"
        ;;
esac
