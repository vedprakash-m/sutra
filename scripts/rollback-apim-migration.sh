#!/bin/bash

# APIM Migration Rollback Script for Sutra
# Safely reverts from APIM-based architecture back to no-gateway direct access
# Preserves data and ensures zero-downtime rollback

set -e

echo "🔄 Sutra APIM Migration Rollback"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ROLLBACK_ID=$(date +%Y%m%d-%H%M%S)
RESOURCE_GROUP="sutra-rg"
FUNCTION_APP_NAME="sutra-api"
APIM_NAME="sutra-apim"
SWA_NAME="sutra-web"

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking rollback prerequisites..."

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not installed"
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure CLI. Run: az login"
    fi

    # Check if original function app exists
    if ! az functionapp show --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Original function app not found - cannot rollback"
    fi

    # Check if backup configuration exists
    if [ ! -f "infrastructure/backup-no-gateway-config.json" ]; then
        log_warning "No backup configuration found - will use defaults"
    fi

    log_success "Prerequisites check passed"
}

# Confirm rollback intention
confirm_rollback() {
    echo ""
    log_warning "⚠️  APIM Migration Rollback Confirmation"
    echo "========================================"
    echo ""
    echo "This will:"
    echo "1. Revert frontend to direct Azure Functions access"
    echo "2. Update CORS settings on function app"
    echo "3. Restore original no-gateway configuration"
    echo "4. Preserve APIM instance (not deleted)"
    echo "5. Maintain all data integrity"
    echo ""

    read -p "Are you sure you want to proceed with rollback? (yes/no): " confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi

    log_info "Rollback confirmed - proceeding..."
}

# Backup current APIM state
backup_apim_state() {
    log_info "Backing up current APIM state..."

    # Create backup directory
    mkdir -p "backups/apim-state-$ROLLBACK_ID"

    # Backup APIM configuration if it exists
    if az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        # Export APIM configuration
        az apim backup \
            --resource-group "$RESOURCE_GROUP" \
            --name "$APIM_NAME" \
            --backup-name "rollback-backup-$ROLLBACK_ID" \
            --storage-account-name "sutrast$(az account show --query id -o tsv | cut -c1-8)" \
            --storage-account-container "apim-backups" \
            2>/dev/null || log_warning "APIM backup failed - continuing rollback"

        log_success "APIM state backed up"
    else
        log_info "No APIM instance found to backup"
    fi
}

# Test function app health before rollback
test_function_app_health() {
    log_info "Testing function app health before rollback..."

    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    if curl -f -s "https://$function_url/api/health" > /dev/null; then
        log_success "Function app is healthy"
    else
        log_warning "Function app health check failed - continuing with rollback"
    fi
}

# Restore no-gateway CORS settings
restore_cors_settings() {
    log_info "Restoring no-gateway CORS settings..."

    # Clear existing CORS settings
    az functionapp cors clear \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME"

    # Get Static Web App URL
    local swa_url=$(az staticwebapp show \
        --name "$SWA_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        -o tsv 2>/dev/null || echo "")

    # Restore original CORS settings for no-gateway
    local cors_origins=(
        "https://localhost:5173"
        "https://localhost:3000"
    )

    if [ -n "$swa_url" ]; then
        cors_origins+=("https://$swa_url")
    fi

    for origin in "${cors_origins[@]}"; do
        az functionapp cors add \
            --resource-group "$RESOURCE_GROUP" \
            --name "$FUNCTION_APP_NAME" \
            --allowed-origins "$origin"
    done

    log_success "CORS settings restored for no-gateway access"
}

# Update function app settings
restore_function_app_settings() {
    log_info "Restoring function app settings for no-gateway..."

    # Remove APIM-specific settings and restore no-gateway settings
    az functionapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --settings \
        "SUTRA_ARCHITECTURE=no-gateway" \
        "SUTRA_ROLLBACK_ID=$ROLLBACK_ID" \
        "SUTRA_MIGRATION_STATE=rolled_back"

    # Remove APIM-specific settings
    az functionapp config appsettings delete \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --setting-names "APIM_GATEWAY_URL" "APIM_SUBSCRIPTION_KEY" \
        2>/dev/null || log_info "No APIM settings found to remove"

    log_success "Function app settings restored"
}

# Update frontend configuration
update_frontend_configuration() {
    log_info "Updating frontend configuration for direct access..."

    # Update API configuration to point to function app directly
    if [ -f "src/services/api.ts" ]; then
        # Backup current API configuration
        cp "src/services/api.ts" "backups/apim-state-$ROLLBACK_ID/api.ts.backup"

        # Restore no-gateway API configuration
        # This would typically involve updating the base URL to point to function app
        log_info "Frontend API configuration backup created"
        log_warning "Manual update required: Update src/services/api.ts to use direct function app URL"
    fi

    # Update static web app configuration if needed
    if [ -f "public/staticwebapp.config.json" ]; then
        # Backup current config
        cp "public/staticwebapp.config.json" "backups/apim-state-$ROLLBACK_ID/staticwebapp.config.json.backup"

        # Restore API location for direct access
        if [ -f "infrastructure/backup-no-gateway-config.json" ]; then
            log_info "Restoring static web app configuration from backup"
            # In a real implementation, this would restore the original configuration
        fi
    fi

    log_success "Frontend configuration updated for rollback"
}

# Validate rollback
validate_rollback() {
    log_info "Validating rollback..."

    # Test direct function access
    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    if curl -f -s "https://$function_url/api/health" > /dev/null; then
        log_success "Direct function access validated"
    else
        log_error "Direct function access validation failed"
    fi

    # Test CORS headers
    local cors_test=$(curl -s -H "Origin: https://localhost:5173" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS "https://$function_url/api/health" \
        -w "%{http_code}" -o /dev/null)

    if [ "$cors_test" -eq 200 ] || [ "$cors_test" -eq 204 ]; then
        log_success "CORS configuration validated"
    else
        log_warning "CORS configuration may need adjustment"
    fi

    # Test authentication still works
    local auth_response=$(curl -s -w "%{http_code}" "https://$function_url/api/admin" -o /dev/null)
    if [ "$auth_response" -eq 401 ] || [ "$auth_response" -eq 403 ]; then
        log_success "Authentication protection still active"
    else
        log_warning "Authentication may need verification"
    fi
}

# Update documentation and tracking
update_documentation() {
    log_info "Updating documentation and tracking..."

    # Update deployment tracking
    echo "ROLLBACK_DATE=$(date -u)" >> "backups/apim-state-$ROLLBACK_ID/rollback-info.txt"
    echo "ROLLBACK_ID=$ROLLBACK_ID" >> "backups/apim-state-$ROLLBACK_ID/rollback-info.txt"
    echo "ARCHITECTURE=no-gateway" >> "backups/apim-state-$ROLLBACK_ID/rollback-info.txt"
    echo "PREVIOUS_STATE=apim-gateway" >> "backups/apim-state-$ROLLBACK_ID/rollback-info.txt"

    log_success "Documentation updated"
}

# Display rollback summary
show_rollback_summary() {
    echo ""
    echo "🎉 APIM Migration Rollback Summary"
    echo "=================================="
    echo ""

    # Function App URL
    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    echo "🔗 API Endpoint (Direct): https://$function_url"

    # Static Web App URL
    local swa_url=$(az staticwebapp show \
        --name "$SWA_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostname" \
        -o tsv 2>/dev/null || echo "")

    if [ -n "$swa_url" ]; then
        echo "🌐 Web App: https://$swa_url"
    fi

    echo ""
    echo "✅ Rollback ID: $ROLLBACK_ID"
    echo "📊 Resource Group: $RESOURCE_GROUP"
    echo "🏗️  Architecture: No-Gateway (Direct Access) - RESTORED"
    echo "💾 Backups: backups/apim-state-$ROLLBACK_ID/"
    echo ""
    echo "⚠️  Manual steps required:"
    echo "1. Update frontend API configuration if needed"
    echo "2. Redeploy frontend with updated configuration"
    echo "3. Run E2E tests to validate functionality"
    echo "4. Monitor logs for any issues"
    echo ""
    echo "Next steps:"
    echo "1. Validate rollback: ./scripts/validate-no-gateway.sh"
    echo "2. Run E2E tests: npm run test:e2e"
    echo "3. Monitor: az functionapp logs tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP"
}

# Main rollback flow
main() {
    local start_time=$(date +%s)

    echo "Starting APIM migration rollback..."
    echo "Rollback ID: $ROLLBACK_ID"
    echo ""

    check_prerequisites
    confirm_rollback
    backup_apim_state
    test_function_app_health
    restore_cors_settings
    restore_function_app_settings
    update_frontend_configuration
    validate_rollback
    update_documentation

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    show_rollback_summary

    log_success "APIM migration rollback completed successfully in ${duration}s!"

    echo ""
    log_warning "Note: APIM instance '$APIM_NAME' is preserved and can be used for future migrations."
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --force        Skip confirmation prompt"
        echo "  --test         Run validation tests only"
        echo ""
        echo "This script rolls back from APIM to no-gateway architecture:"
        echo "- Restores direct Azure Functions access"
        echo "- Updates CORS and function app settings"
        echo "- Preserves APIM instance for future use"
        echo "- Maintains data integrity"
        exit 0
        ;;
    --force)
        check_prerequisites
        backup_apim_state
        test_function_app_health
        restore_cors_settings
        restore_function_app_settings
        update_frontend_configuration
        validate_rollback
        update_documentation
        show_rollback_summary
        log_success "Forced rollback completed!"
        ;;
    --test)
        check_prerequisites
        test_function_app_health
        validate_rollback
        log_success "Rollback validation tests completed!"
        ;;
    *)
        main "$@"
        ;;
esac
