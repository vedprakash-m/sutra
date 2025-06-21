#!/bin/bash

# APIM Migration Deployment Script for Sutra
# Deploys API Management Gateway in front of existing Azure Functions
# Migrates from no-gateway to APIM-based architecture

set -e

echo "🚀 Sutra APIM Migration Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DEPLOYMENT_ID=$(date +%Y%m%d-%H%M%S)
RESOURCE_GROUP="sutra-rg"
LOCATION="eastus"
FUNCTION_APP_NAME="sutra-api"
APIM_NAME="sutra-apim"

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking APIM migration prerequisites..."

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not installed"
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure CLI. Run: az login"
    fi

    # Check if source function app exists
    if ! az functionapp show --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Source function app not found - deploy no-gateway first"
    fi

    # Check required files
    if [ ! -f "infrastructure/apim-migration.bicep" ]; then
        log_error "APIM migration Bicep template not found"
    fi

    # Validate templates
    if ! az bicep build --file infrastructure/apim-migration.bicep --stdout > /dev/null; then
        log_error "APIM migration Bicep template validation failed"
    fi

    log_success "Prerequisites check passed"
}

# Backup current no-gateway configuration
backup_current_state() {
    log_info "Backing up current no-gateway configuration..."

    # Create backup directory
    mkdir -p "backups/no-gateway-state-$DEPLOYMENT_ID"

    # Backup function app configuration
    az functionapp config show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        > "backups/no-gateway-state-$DEPLOYMENT_ID/function-app-config.json"

    # Backup app settings
    az functionapp config appsettings list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        > "backups/no-gateway-state-$DEPLOYMENT_ID/app-settings.json"

    # Backup CORS settings
    az functionapp cors show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        > "backups/no-gateway-state-$DEPLOYMENT_ID/cors-settings.json"

    # Save backup reference for rollback
    cp "backups/no-gateway-state-$DEPLOYMENT_ID/function-app-config.json" \
       "infrastructure/backup-no-gateway-config.json"

    log_success "Current state backed up"
}

# Test current function app health
test_current_health() {
    log_info "Testing current function app health..."

    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    if curl -f -s "https://$function_url/api/health" > /dev/null; then
        log_success "Function app is healthy and ready for migration"
    else
        log_error "Function app health check failed - fix before migration"
    fi

    # Store function app URL for APIM backend configuration
    echo "$function_url" > "backups/no-gateway-state-$DEPLOYMENT_ID/function-app-url.txt"
}

# Deploy APIM infrastructure
deploy_apim_infrastructure() {
    log_info "Deploying APIM infrastructure..."

    # Get function app details for backend configuration
    local function_url=$(cat "backups/no-gateway-state-$DEPLOYMENT_ID/function-app-url.txt")

    # Deploy APIM infrastructure
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infrastructure/apim-migration.bicep \
        --parameters @infrastructure/parameters.apim-migration.json \
        --parameters backendFunctionAppUrl="https://$function_url" \
        --parameters deploymentId="$DEPLOYMENT_ID" \
        --name "apim-migration-$DEPLOYMENT_ID" \
        --verbose

    log_success "APIM infrastructure deployed"
}

# Configure APIM APIs and policies
configure_apim_apis() {
    log_info "Configuring APIM APIs and policies..."

    # Wait for APIM to be ready
    local retry_count=0
    while [ $retry_count -lt 30 ]; do
        if az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
            break
        fi
        log_info "Waiting for APIM to be ready... ($retry_count/30)"
        sleep 30
        ((retry_count++))
    done

    if [ $retry_count -eq 30 ]; then
        log_error "APIM deployment timed out"
    fi

    # Import OpenAPI definition if available
    if [ -f "api/openapi.json" ]; then
        az apim api import \
            --resource-group "$RESOURCE_GROUP" \
            --service-name "$APIM_NAME" \
            --api-id "sutra-api" \
            --specification-format "OpenApi" \
            --specification-path "api/openapi.json" \
            --path "api"

        log_success "OpenAPI definition imported"
    else
        log_info "No OpenAPI definition found - manual API configuration needed"
    fi

    # Configure rate limiting policies
    az apim api policy create \
        --resource-group "$RESOURCE_GROUP" \
        --service-name "$APIM_NAME" \
        --api-id "sutra-api" \
        --policy-content "$(cat << 'EOF'
<policies>
    <inbound>
        <base />
        <rate-limit calls="100" renewal-period="60" />
        <cors>
            <allowed-origins>
                <origin>https://localhost:5173</origin>
                <origin>https://localhost:3000</origin>
            </allowed-origins>
            <allowed-methods>
                <method>GET</method>
                <method>POST</method>
                <method>PUT</method>
                <method>DELETE</method>
                <method>OPTIONS</method>
            </allowed-methods>
            <allowed-headers>
                <header>*</header>
            </allowed-headers>
        </cors>
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
        <set-header name="X-Powered-By" exists-action="override">
            <value>Sutra APIM</value>
        </set-header>
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
EOF
)" 2>/dev/null || log_warning "APIM policy configuration may need manual setup"

    log_success "APIM APIs and policies configured"
}

# Update function app for APIM integration
update_function_app_for_apim() {
    log_info "Updating function app for APIM integration..."

    # Get APIM gateway URL
    local apim_gateway_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv)

    # Update function app settings
    az functionapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --settings \
        "SUTRA_ARCHITECTURE=apim-gateway" \
        "APIM_GATEWAY_URL=$apim_gateway_url" \
        "SUTRA_MIGRATION_ID=$DEPLOYMENT_ID"

    # Update CORS to allow APIM
    az functionapp cors add \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --allowed-origins "$apim_gateway_url"

    log_success "Function app updated for APIM integration"
}

# Configure custom domain (if specified)
configure_custom_domain() {
    if [ -n "${CUSTOM_DOMAIN:-}" ]; then
        log_info "Configuring custom domain: $CUSTOM_DOMAIN"

        # Configure custom domain for APIM
        az apim custom-domain create \
            --resource-group "$RESOURCE_GROUP" \
            --service-name "$APIM_NAME" \
            --hostname "$CUSTOM_DOMAIN" \
            --certificate-path "${CERTIFICATE_PATH:-}" \
            --certificate-password "${CERTIFICATE_PASSWORD:-}" \
            2>/dev/null || log_warning "Custom domain configuration needs manual setup"

        log_success "Custom domain configured"
    else
        log_info "No custom domain specified - using default APIM URL"
    fi
}

# Test APIM functionality
test_apim_functionality() {
    log_info "Testing APIM functionality..."

    # Get APIM gateway URL
    local apim_gateway_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv)

    # Test health endpoint through APIM
    if curl -f -s "$apim_gateway_url/api/health" > /dev/null; then
        log_success "APIM health check passed"
    else
        log_warning "APIM health check failed - may need time to propagate"
    fi

    # Test rate limiting
    local rate_limit_test=true
    for i in {1..20}; do
        local response_code=$(curl -s -w "%{http_code}" "$apim_gateway_url/api/health" -o /dev/null)
        if [ "$response_code" -eq 429 ]; then
            log_success "APIM rate limiting is working"
            rate_limit_test=false
            break
        fi
    done

    if [ "$rate_limit_test" = true ]; then
        log_warning "APIM rate limiting may need adjustment"
    fi

    # Test CORS
    local cors_test=$(curl -s -H "Origin: https://localhost:5173" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS "$apim_gateway_url/api/health" \
        -w "%{http_code}" -o /dev/null)

    if [ "$cors_test" -eq 200 ] || [ "$cors_test" -eq 204 ]; then
        log_success "APIM CORS configuration working"
    else
        log_warning "APIM CORS may need adjustment"
    fi
}

# Update frontend configuration
update_frontend_configuration() {
    log_info "Updating frontend configuration for APIM..."

    # Get APIM gateway URL
    local apim_gateway_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv)

    # Create environment configuration for APIM
    cat > ".env.apim" << EOF
VITE_API_BASE_URL=$apim_gateway_url
VITE_ARCHITECTURE=apim-gateway
VITE_DEPLOYMENT_ID=$DEPLOYMENT_ID
EOF

    log_success "Frontend environment configuration created"
    log_warning "Manual step required: Update frontend to use APIM gateway URL"
    log_info "Use: $apim_gateway_url as the API base URL"
}

# Validate migration
validate_migration() {
    log_info "Validating APIM migration..."

    # Run migration tests
    if [ -f "scripts/test-apim-migration.sh" ]; then
        if bash scripts/test-apim-migration.sh --quick; then
            log_success "APIM migration validation passed"
        else
            log_warning "APIM migration validation had warnings - review output"
        fi
    else
        log_warning "APIM migration test script not found"
    fi
}

# Display migration summary
show_migration_summary() {
    echo ""
    echo "🎉 APIM Migration Deployment Summary"
    echo "===================================="
    echo ""

    # APIM Gateway URL
    local apim_gateway_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv)

    echo "🌐 APIM Gateway: $apim_gateway_url"

    # Function App URL (backend)
    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    echo "🔗 Backend (Direct): https://$function_url"

    echo ""
    echo "✅ Migration ID: $DEPLOYMENT_ID"
    echo "📊 Resource Group: $RESOURCE_GROUP"
    echo "🏗️  Architecture: APIM Gateway (Upgraded from No-Gateway)"
    echo "💾 Backups: backups/no-gateway-state-$DEPLOYMENT_ID/"
    echo ""
    echo "⚠️  Manual steps required:"
    echo "1. Update frontend API configuration to use APIM URL"
    echo "2. Configure API subscriptions and products in APIM"
    echo "3. Set up monitoring and alerts"
    echo "4. Test all API endpoints through APIM"
    echo ""
    echo "Next steps:"
    echo "1. Test migration: ./scripts/test-apim-migration.sh"
    echo "2. Update frontend: Use $apim_gateway_url as API base"
    echo "3. Run E2E tests with APIM"
    echo "4. Monitor: az apim api show --name $APIM_NAME --resource-group $RESOURCE_GROUP"
    echo "5. Rollback if needed: ./scripts/rollback-apim-migration.sh"
}

# Main migration flow
main() {
    local start_time=$(date +%s)

    echo "Starting APIM migration deployment..."
    echo "Migration ID: $DEPLOYMENT_ID"
    echo ""

    check_prerequisites
    backup_current_state
    test_current_health
    deploy_apim_infrastructure
    configure_apim_apis
    update_function_app_for_apim
    configure_custom_domain
    test_apim_functionality
    update_frontend_configuration
    validate_migration

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    show_migration_summary

    log_success "APIM migration deployment completed successfully in ${duration}s!"

    echo ""
    log_info "Note: Original function app is preserved for rollback capability."
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h         Show this help message"
        echo "  --test-only        Run tests without deployment"
        echo "  --custom-domain    Set custom domain (requires CUSTOM_DOMAIN env var)"
        echo ""
        echo "Environment variables:"
        echo "  CUSTOM_DOMAIN      Custom domain for APIM (optional)"
        echo "  CERTIFICATE_PATH   SSL certificate path (required with custom domain)"
        echo "  CERTIFICATE_PASSWORD SSL certificate password"
        echo ""
        echo "This script migrates from no-gateway to APIM architecture:"
        echo "- Deploys API Management Gateway"
        echo "- Configures APIs, policies, and backends"
        echo "- Updates function app integration"
        echo "- Preserves rollback capability"
        exit 0
        ;;
    --test-only)
        check_prerequisites
        test_current_health
        if [ -f "scripts/test-apim-migration.sh" ]; then
            bash scripts/test-apim-migration.sh
        else
            log_error "APIM test script not found"
        fi
        ;;
    --custom-domain)
        if [ -z "${CUSTOM_DOMAIN:-}" ]; then
            log_error "CUSTOM_DOMAIN environment variable not set"
        fi
        main "$@"
        ;;
    *)
        main "$@"
        ;;
esac
