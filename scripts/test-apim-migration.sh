#!/bin/bash

# APIM Migration Test Script for Sutra
# Tests the migration from no-gateway to APIM-based architecture
# Validates compatibility, functionality, and performance

set -e

echo "🧪 Sutra APIM Migration Testing"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TEST_RESULTS=()
ISSUES_FOUND=0
START_TIME=$(date +%s)

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; TEST_RESULTS+=("PASS: $1"); }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; TEST_RESULTS+=("WARN: $1"); }
log_error() { echo -e "${RED}❌ $1${NC}"; ((ISSUES_FOUND++)); TEST_RESULTS+=("FAIL: $1"); }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Configuration
RESOURCE_GROUP="sutra-rg"
FUNCTION_APP_NAME="sutra-api"
APIM_NAME="sutra-apim"
SWA_NAME="sutra-web"

# Test prerequisites
test_prerequisites() {
    log_info "Testing migration prerequisites..."

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not installed"
        return 1
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure CLI"
        return 1
    fi

    # Check if both architectures exist
    if az functionapp show --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Source function app exists"
    else
        log_error "Source function app not found"
    fi

    if az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Target APIM instance exists"
    else
        log_warning "APIM instance not found - migration target missing"
    fi

    # Check migration templates
    if [ -f "infrastructure/apim-migration.bicep" ]; then
        log_success "APIM migration template exists"
    else
        log_error "APIM migration template missing"
    fi
}

# Test direct function access (pre-migration)
test_direct_function_access() {
    log_info "Testing direct function access (pre-migration state)..."

    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    if [ -z "$function_url" ]; then
        log_error "Cannot get function app URL"
        return 1
    fi

    # Test health endpoint
    if curl -f -s "https://$function_url/api/health" > /dev/null; then
        log_success "Direct function health check passed"
    else
        log_error "Direct function health check failed"
    fi

    # Test authentication
    local auth_response=$(curl -s -w "%{http_code}" "https://$function_url/api/admin" -o /dev/null)
    if [ "$auth_response" -eq 401 ] || [ "$auth_response" -eq 403 ]; then
        log_success "Authentication protection working on direct access"
    else
        log_warning "Authentication may not be properly configured"
    fi

    # Test rate limiting
    local rate_limit_test=true
    for i in {1..20}; do
        if ! curl -f -s "https://$function_url/api/health" > /dev/null; then
            rate_limit_test=false
            break
        fi
    done

    if [ "$rate_limit_test" = true ]; then
        log_warning "Rate limiting may not be active (20 rapid requests succeeded)"
    else
        log_success "Rate limiting appears to be working"
    fi
}

# Test APIM configuration
test_apim_configuration() {
    log_info "Testing APIM configuration..."

    if ! az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_warning "APIM instance not deployed yet"
        return 0
    fi

    # Test APIM policies
    local policies=$(az apim api policy list \
        --resource-group "$RESOURCE_GROUP" \
        --service-name "$APIM_NAME" \
        --api-id "sutra-api" \
        --query "length(@)" \
        -o tsv 2>/dev/null || echo "0")

    if [ "$policies" -gt 0 ]; then
        log_success "APIM policies configured"
    else
        log_warning "No APIM policies found"
    fi

    # Test backend configuration
    local backends=$(az apim backend list \
        --resource-group "$RESOURCE_GROUP" \
        --service-name "$APIM_NAME" \
        --query "length(@)" \
        -o tsv 2>/dev/null || echo "0")

    if [ "$backends" -gt 0 ]; then
        log_success "APIM backends configured"
    else
        log_warning "No APIM backends found"
    fi

    # Test product configuration
    local products=$(az apim product list \
        --resource-group "$RESOURCE_GROUP" \
        --service-name "$APIM_NAME" \
        --query "length(@)" \
        -o tsv 2>/dev/null || echo "0")

    if [ "$products" -gt 0 ]; then
        log_success "APIM products configured"
    else
        log_warning "No APIM products found"
    fi
}

# Test API compatibility between direct and APIM access
test_api_compatibility() {
    log_info "Testing API compatibility between direct and APIM access..."

    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    local apim_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv 2>/dev/null || echo "")

    if [ -z "$apim_url" ]; then
        log_warning "APIM URL not available for comparison"
        return 0
    fi

    # Compare health endpoint responses
    local direct_health=$(curl -s "https://$function_url/api/health" || echo "ERROR")
    local apim_health=$(curl -s "$apim_url/api/health" || echo "ERROR")

    if [ "$direct_health" = "$apim_health" ] && [ "$direct_health" != "ERROR" ]; then
        log_success "Health endpoint responses match between direct and APIM"
    else
        log_error "Health endpoint responses differ between direct and APIM"
    fi

    # Test response headers
    local direct_headers=$(curl -s -I "https://$function_url/api/health" | grep -i "content-type" || echo "")
    local apim_headers=$(curl -s -I "$apim_url/api/health" | grep -i "content-type" || echo "")

    if [ -n "$direct_headers" ] && [ -n "$apim_headers" ]; then
        log_success "Both endpoints return proper headers"
    else
        log_warning "Header comparison inconclusive"
    fi
}

# Test migration rollback capability
test_rollback_capability() {
    log_info "Testing migration rollback capability..."

    # Check if rollback script exists
    if [ -f "scripts/rollback-apim-migration.sh" ]; then
        log_success "Rollback script exists"

        # Validate rollback script syntax
        if bash -n "scripts/rollback-apim-migration.sh"; then
            log_success "Rollback script syntax is valid"
        else
            log_error "Rollback script has syntax errors"
        fi
    else
        log_error "Rollback script missing"
    fi

    # Check if backup configuration exists
    if [ -f "infrastructure/backup-no-gateway-config.json" ]; then
        log_success "Backup configuration exists"
    else
        log_warning "No backup configuration found"
    fi
}

# Test performance impact
test_performance_impact() {
    log_info "Testing performance impact of APIM migration..."

    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    # Test direct access latency
    local direct_latency=$(curl -s -w "%{time_total}" "https://$function_url/api/health" -o /dev/null)

    # Test APIM access latency (if available)
    local apim_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv 2>/dev/null || echo "")

    if [ -n "$apim_url" ]; then
        local apim_latency=$(curl -s -w "%{time_total}" "$apim_url/api/health" -o /dev/null)

        # Compare latencies (allowing for some overhead)
        local latency_diff=$(echo "$apim_latency - $direct_latency" | bc -l 2>/dev/null || echo "0")

        if [ "$(echo "$latency_diff < 0.5" | bc -l 2>/dev/null || echo "1")" -eq 1 ]; then
            log_success "APIM latency overhead is acceptable (${latency_diff}s)"
        else
            log_warning "APIM adds significant latency overhead (${latency_diff}s)"
        fi
    else
        log_info "APIM not available for latency comparison"
    fi

    log_info "Direct access latency: ${direct_latency}s"
}

# Test security enhancements
test_security_enhancements() {
    log_info "Testing security enhancements with APIM..."

    # Test if APIM adds security headers
    local apim_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv 2>/dev/null || echo "")

    if [ -n "$apim_url" ]; then
        # Check for security headers
        local security_headers=$(curl -s -I "$apim_url/api/health" | grep -i -E "(x-content-type-options|x-frame-options|strict-transport-security)")

        if [ -n "$security_headers" ]; then
            log_success "APIM adds security headers"
        else
            log_warning "APIM may not be adding security headers"
        fi

        # Test rate limiting through APIM
        local rate_limit_test=true
        for i in {1..30}; do
            local response_code=$(curl -s -w "%{http_code}" "$apim_url/api/health" -o /dev/null)
            if [ "$response_code" -eq 429 ]; then
                log_success "APIM rate limiting is working"
                rate_limit_test=false
                break
            fi
        done

        if [ "$rate_limit_test" = true ]; then
            log_warning "APIM rate limiting may not be configured"
        fi
    else
        log_info "APIM not available for security testing"
    fi
}

# Test static web app integration
test_swa_integration() {
    log_info "Testing Static Web App integration with migration..."

    # Check if SWA exists
    if ! az staticwebapp show --name "$SWA_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_warning "Static Web App not found"
        return 0
    fi

    # Check SWA configuration for API location
    if [ -f "public/staticwebapp.config.json" ]; then
        local api_location=$(jq -r '.apiLocation // empty' public/staticwebapp.config.json 2>/dev/null)

        if [ -n "$api_location" ]; then
            log_success "SWA API location configured: $api_location"
        else
            log_warning "SWA API location not configured"
        fi
    fi

    # Test frontend API configuration
    if [ -f "src/services/api.ts" ]; then
        if grep -q "apim\|gateway" src/services/api.ts; then
            log_success "Frontend configured for APIM gateway"
        else
            log_info "Frontend still configured for direct access"
        fi
    fi
}

# Test migration data consistency
test_data_consistency() {
    log_info "Testing data consistency during migration..."

    # Test database connections through both paths
    local function_url=$(az functionapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --query "defaultHostName" \
        -o tsv)

    # Test direct database access
    local direct_db_test=$(curl -s "https://$function_url/api/collections" -H "Authorization: Bearer test" | jq -r '.status // "error"' 2>/dev/null || echo "error")

    # Test APIM database access (if available)
    local apim_url=$(az apim show \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "gatewayUrl" \
        -o tsv 2>/dev/null || echo "")

    if [ -n "$apim_url" ]; then
        local apim_db_test=$(curl -s "$apim_url/api/collections" -H "Authorization: Bearer test" | jq -r '.status // "error"' 2>/dev/null || echo "error")

        if [ "$direct_db_test" = "$apim_db_test" ]; then
            log_success "Database responses consistent between direct and APIM"
        else
            log_warning "Database responses may differ between direct and APIM"
        fi
    else
        log_info "APIM not available for data consistency testing"
    fi
}

# Generate migration test report
generate_test_report() {
    echo ""
    echo "📊 APIM Migration Test Report"
    echo "============================"
    echo ""

    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    echo "Test Duration: ${duration}s"
    echo "Issues Found: $ISSUES_FOUND"
    echo ""
    echo "Test Results:"
    echo "============"

    for result in "${TEST_RESULTS[@]}"; do
        if [[ $result == PASS:* ]]; then
            echo -e "${GREEN}✅ ${result#PASS: }${NC}"
        elif [[ $result == WARN:* ]]; then
            echo -e "${YELLOW}⚠️  ${result#WARN: }${NC}"
        elif [[ $result == FAIL:* ]]; then
            echo -e "${RED}❌ ${result#FAIL: }${NC}"
        fi
    done

    echo ""

    if [ $ISSUES_FOUND -eq 0 ]; then
        echo -e "${GREEN}🎉 All critical tests passed! Migration is ready.${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Deploy APIM: ./scripts/deploy-apim-migration.sh"
        echo "2. Update frontend configuration for APIM"
        echo "3. Run E2E tests with APIM enabled"
        echo "4. Monitor performance and rollback if needed"
    else
        echo -e "${RED}⚠️  $ISSUES_FOUND critical issues found. Review before migration.${NC}"
        echo ""
        echo "Recommended actions:"
        echo "1. Fix critical issues identified above"
        echo "2. Re-run tests: ./scripts/test-apim-migration.sh"
        echo "3. Consider staged migration approach"
    fi
}

# Main test execution
main() {
    echo "Starting APIM migration tests..."
    echo ""

    test_prerequisites
    test_direct_function_access
    test_apim_configuration
    test_api_compatibility
    test_rollback_capability
    test_performance_impact
    test_security_enhancements
    test_swa_integration
    test_data_consistency

    generate_test_report

    exit $ISSUES_FOUND
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h         Show this help message"
        echo "  --quick           Run quick tests only"
        echo "  --performance     Run performance tests only"
        echo "  --security        Run security tests only"
        echo ""
        echo "This script tests APIM migration readiness and compatibility."
        exit 0
        ;;
    --quick)
        test_prerequisites
        test_direct_function_access
        test_apim_configuration
        generate_test_report
        exit $ISSUES_FOUND
        ;;
    --performance)
        test_prerequisites
        test_performance_impact
        generate_test_report
        exit $ISSUES_FOUND
        ;;
    --security)
        test_prerequisites
        test_security_enhancements
        generate_test_report
        exit $ISSUES_FOUND
        ;;
    *)
        main "$@"
        ;;
esac
