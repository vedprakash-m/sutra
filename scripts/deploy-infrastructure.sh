#!/bin/bash

# Sutra Infrastructure Deployment Script
# Deploys direct access architecture optimized for small teams

set -euo pipefail

# Configuration
RESOURCE_GROUP="sutra-rg"
LOCATION="eastus2"
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infrastructure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Check subscription
    if [[ -n "$SUBSCRIPTION_ID" ]]; then
        log_info "Setting subscription to: $SUBSCRIPTION_ID"
        az account set --subscription "$SUBSCRIPTION_ID"
    fi
    
    # Verify resource group exists
    if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Resource group '$RESOURCE_GROUP' does not exist."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Check for existing Front Door
check_existing_front_door() {
    log_info "Checking for existing Front Door resources..."
    
    local front_door_count
    front_door_count=$(az afd profile list --resource-group "$RESOURCE_GROUP" --query "length([])" --output tsv 2>/dev/null || echo "0")
    
    if [[ "$front_door_count" -gt 0 ]]; then
        log_warning "Found $front_door_count Front Door profile(s) in resource group"
        echo ""
        echo "Existing Front Door profiles:"
        az afd profile list --resource-group "$RESOURCE_GROUP" --query "[].{Name:name, Status:provisioningState}" --output table
        echo ""
        read -p "Do you want to remove these Front Door resources? (y/N): " remove_fd
        
        if [[ "$remove_fd" =~ ^[Yy]$ ]]; then
            remove_front_door_resources
        else
            log_info "Keeping existing Front Door resources. They will coexist with the new architecture."
        fi
    else
        log_info "No existing Front Door resources found"
    fi
}

# Remove Front Door resources
remove_front_door_resources() {
    log_info "Removing Front Door resources..."
    
    # Get all Front Door profiles
    local profiles
    profiles=$(az afd profile list --resource-group "$RESOURCE_GROUP" --query "[].name" --output tsv)
    
    if [[ -n "$profiles" ]]; then
        echo "$profiles" | while read -r profile; do
            log_info "Deleting Front Door profile: $profile"
            az afd profile delete \
                --resource-group "$RESOURCE_GROUP" \
                --profile-name "$profile" \
                --yes
        done
        log_success "Front Door resources removed"
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure..."
    
    local deployment_name="compute-$(date +%Y%m%d-%H%M%S)"
    
    # Deploy the compute template
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$deployment_name" \
        --template-file "${INFRA_DIR}/compute.bicep" \
        --parameters "@${INFRA_DIR}/parameters.compute.json" \
        --verbose
    
    if [[ $? -eq 0 ]]; then
        log_success "Infrastructure deployment completed successfully"
        return 0
    else
        log_error "Infrastructure deployment failed"
        return 1
    fi
}

# Get deployment outputs
get_deployment_outputs() {
    log_info "Retrieving deployment outputs..."
    
    # Get the latest deployment
    local latest_deployment
    latest_deployment=$(az deployment group list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?starts_with(name, 'compute')] | sort_by(@, &properties.timestamp) | [-1].name" \
        --output tsv)
    
    if [[ -n "$latest_deployment" ]]; then
        log_info "Latest deployment: $latest_deployment"
        
        # Get outputs
        local function_url static_url api_base_url
        function_url=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.functionAppUrl.value" \
            --output tsv)
        
        static_url=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.staticWebAppUrl.value" \
            --output tsv)
        
        api_base_url=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.apiBaseUrl.value" \
            --output tsv)
        
        echo ""
        log_success "Deployment outputs:"
        echo "  Static Web App URL: $static_url"
        echo "  Function App URL: $function_url"
        echo "  API Base URL: $api_base_url"
        echo ""
        
        # Save outputs for frontend configuration
        cat > "${SCRIPT_DIR}/../.env.production" << EOF
# Production environment variables for no-gateway architecture
VITE_API_URL=$api_base_url
VITE_APP_URL=$static_url
VITE_ENVIRONMENT=production
VITE_ARCHITECTURE=no-gateway
EOF
        
        log_success "Environment variables saved to .env.production"
        
    else
        log_warning "No deployment found"
    fi
}

# Configure Static Web App authentication
configure_authentication() {
    log_info "Configuring Static Web App authentication..."
    
    local static_app_name="sutra-web"
    
    # Check if Azure AD app registration is needed
    echo ""
    log_info "Authentication setup required:"
    echo "1. Create an Azure AD app registration"
    echo "2. Configure redirect URIs"
    echo "3. Set environment variables in Static Web App"
    echo ""
    echo "Required environment variables:"
    echo "  AZURE_CLIENT_ID=<your-app-registration-client-id>"
    echo "  AZURE_CLIENT_SECRET=<your-app-registration-client-secret>"
    echo ""
    
    read -p "Do you want to configure authentication now? (y/N): " configure_auth
    
    if [[ "$configure_auth" =~ ^[Yy]$ ]]; then
        echo ""
        read -p "Enter Azure AD Client ID: " client_id
        read -s -p "Enter Azure AD Client Secret: " client_secret
        echo ""
        
        if [[ -n "$client_id" && -n "$client_secret" ]]; then
            # Set Static Web App configuration
            az staticwebapp appsettings set \
                --name "$static_app_name" \
                --resource-group "$RESOURCE_GROUP" \
                --setting-names "AZURE_CLIENT_ID=$client_id" "AZURE_CLIENT_SECRET=$client_secret"
            
            log_success "Authentication configured successfully"
        else
            log_warning "Authentication configuration skipped - missing credentials"
        fi
    else
        log_info "Authentication configuration can be done later through Azure Portal"
    fi
}

# Test endpoints
test_endpoints() {
    log_info "Testing deployed endpoints..."
    
    # Get the latest deployment outputs
    local latest_deployment
    latest_deployment=$(az deployment group list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?starts_with(name, 'no-gateway')] | sort_by(@, &properties.timestamp) | [-1].name" \
        --output tsv)
    
    if [[ -n "$latest_deployment" ]]; then
        local api_base_url static_url
        api_base_url=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.apiBaseUrl.value" \
            --output tsv)
        
        static_url=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.staticWebAppUrl.value" \
            --output tsv)
        
        # Test API health endpoint
        if [[ -n "$api_base_url" ]]; then
            log_info "Testing API health endpoint: ${api_base_url}/health"
            
            local response_code
            response_code=$(curl -s -o /dev/null -w "%{http_code}" "${api_base_url}/health" || echo "000")
            
            if [[ "$response_code" == "200" ]]; then
                log_success "API health check passed (HTTP $response_code)"
            else
                log_warning "API health check returned HTTP $response_code"
                log_info "This might be expected if the Function App is cold starting"
            fi
        fi
        
        # Test Static Web App
        if [[ -n "$static_url" ]]; then
            log_info "Testing Static Web App: $static_url"
            
            local response_code
            response_code=$(curl -s -o /dev/null -w "%{http_code}" "$static_url" || echo "000")
            
            if [[ "$response_code" == "200" ]]; then
                log_success "Static Web App accessible (HTTP $response_code)"
            else
                log_warning "Static Web App returned HTTP $response_code"
            fi
        fi
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    log_success "No-Gateway Architecture Deployment Complete!"
    echo ""
    log_info "Next Steps:"
    echo "1. Update your frontend code and redeploy:"
    echo "   npm run build"
    echo "   # Deploy to Static Web App"
    echo ""
    echo "2. Configure authentication (if not done already):"
    echo "   - Create Azure AD app registration"
    echo "   - Set AZURE_CLIENT_ID and AZURE_CLIENT_SECRET in Static Web App"
    echo ""
    echo "3. Test the application end-to-end:"
    echo "   - Verify login/logout functionality"
    echo "   - Test API endpoints through the frontend"
    echo "   - Monitor Application Insights for any issues"
    echo ""
    echo "4. Optional optimizations:"
    echo "   - Configure custom domain"
    echo "   - Set up additional monitoring alerts"
    echo "   - Implement application-level rate limiting if needed"
    echo ""
    log_info "Documentation: docs/metadata.md"
    log_info "Cost savings: Eliminated Front Door costs (~$70/month)"
}

# Main deployment function
main() {
    log_info "Sutra No-Gateway Architecture Deployment"
    log_info "========================================"
    
    check_prerequisites
    check_existing_front_door
    
    if deploy_infrastructure; then
        get_deployment_outputs
        configure_authentication
        test_endpoints
        show_next_steps
    else
        log_error "Deployment failed. Check the error messages above."
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
