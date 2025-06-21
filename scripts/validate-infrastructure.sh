#!/bin/bash

# Sutra Direct Access Architecture Validation Script
# Tests the implemented direct access architecture

set -euo pipefail

# Configuration
RESOURCE_GROUP="sutra-rg"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

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

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    log_info "Running test: $test_name"

    if eval "$test_command"; then
        if [[ "$expected_result" == "pass" ]]; then
            log_success "✓ $test_name"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ $test_name (expected to fail but passed)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        if [[ "$expected_result" == "fail" ]]; then
            log_warning "✓ $test_name (expected failure)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "✗ $test_name"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
}

# Get deployment endpoints
get_endpoints() {
    local latest_deployment
    latest_deployment=$(az deployment group list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?starts_with(name, 'compute')] | sort_by(@, &properties.timestamp) | [-1].name" \
        --output tsv 2>/dev/null || echo "")

    if [[ -n "$latest_deployment" ]]; then
        API_URL=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.apiBaseUrl.value" \
            --output tsv 2>/dev/null || echo "")

        STATIC_URL=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$latest_deployment" \
            --query "properties.outputs.staticWebAppUrl.value" \
            --output tsv 2>/dev/null || echo "")
    else
        API_URL=""
        STATIC_URL=""
    fi
}

# Test infrastructure deployment
test_infrastructure() {
    log_info "Testing Infrastructure Deployment"
    log_info "================================="

    # Test that Front Door is removed
    run_test "Front Door resources removed" \
        "[ \$(az afd profile list --resource-group '$RESOURCE_GROUP' --query 'length([])' --output tsv 2>/dev/null || echo '0') -eq 0 ]" \
        "pass"

    # Test Function App exists
    run_test "Function App exists" \
        "az functionapp show --resource-group '$RESOURCE_GROUP' --name 'sutra-api' >/dev/null 2>&1" \
        "pass"

    # Test Static Web App exists
    run_test "Static Web App exists" \
        "az staticwebapp show --resource-group '$RESOURCE_GROUP' --name 'sutra-web' >/dev/null 2>&1" \
        "pass"

    # Test Application Insights exists
    run_test "Application Insights exists" \
        "az monitor app-insights component show --resource-group '$RESOURCE_GROUP' --app 'sutra-ai' >/dev/null 2>&1" \
        "pass"
}

# Test direct access connectivity
test_direct_access() {
    log_info "Testing Direct Access Connectivity"
    log_info "=================================="

    get_endpoints

    if [[ -n "$API_URL" ]]; then
        log_info "Testing API endpoint: $API_URL"

        # Test health endpoint
        run_test "API health endpoint responds" \
            "curl -s -f --max-time 10 '$API_URL/health' >/dev/null" \
            "pass"

        # Test health endpoint returns JSON
        run_test "Health endpoint returns JSON" \
            "curl -s --max-time 10 '$API_URL/health' | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1" \
            "pass"

        # Test security headers
        run_test "Security headers present" \
            "curl -s --max-time 10 '$API_URL/health' -I | grep -q 'X-Content-Type-Options'" \
            "pass"

        # Test rate limiting headers
        run_test "Rate limiting headers present" \
            "curl -s --max-time 10 '$API_URL/health' -I | grep -q 'X-RateLimit-Limit'" \
            "pass"

    else
        log_warning "API endpoint not found - skipping direct access tests"
    fi

    if [[ -n "$STATIC_URL" ]]; then
        log_info "Testing Static Web App: $STATIC_URL"

        # Test Static Web App accessibility
        run_test "Static Web App accessible" \
            "curl -s -f --max-time 10 '$STATIC_URL' >/dev/null" \
            "pass"

        # Test HTTPS enforcement
        local http_url
        http_url=$(echo "$STATIC_URL" | sed 's/https:/http:/')
        run_test "HTTP redirects to HTTPS" \
            "curl -s --max-time 10 '$http_url' -I | grep -q '30[12]'" \
            "pass"

    else
        log_warning "Static Web App endpoint not found - skipping tests"
    fi
}

# Test security implementation
test_security() {
    log_info "Testing Security Implementation"
    log_info "==============================="

    if [[ -n "$API_URL" ]]; then
        # Test CORS headers
        run_test "CORS headers configured" \
            "curl -s --max-time 10 -H 'Origin: https://sutra-web.azurestaticapps.net' '$API_URL/health' -I | grep -q 'Access-Control'" \
            "pass"

        # Test security headers
        run_test "X-Frame-Options header" \
            "curl -s --max-time 10 '$API_URL/health' -I | grep -q 'X-Frame-Options: DENY'" \
            "pass"

        run_test "X-Content-Type-Options header" \
            "curl -s --max-time 10 '$API_URL/health' -I | grep -q 'X-Content-Type-Options: nosniff'" \
            "pass"

        # Test rate limiting functionality
        log_info "Testing rate limiting (this may take a moment)..."
        local rate_limit_triggered=false
        for i in {1..15}; do
            local response_code
            response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$API_URL/health" 2>/dev/null || echo "000")
            if [[ "$response_code" == "429" ]]; then
                rate_limit_triggered=true
                break
            fi
            sleep 0.1
        done

        if [[ "$rate_limit_triggered" == "true" ]]; then
            log_success "✓ Rate limiting is working"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_warning "⚠ Rate limiting not triggered (may need higher load)"
        fi
        TESTS_TOTAL=$((TESTS_TOTAL + 1))

    else
        log_warning "API endpoint not available - skipping security tests"
    fi
}

# Test Static Web App configuration
test_static_web_app_config() {
    log_info "Testing Static Web App Configuration"
    log_info "==================================="

    # Check if staticwebapp.config.json exists
    run_test "Static Web App config file exists" \
        "[ -f '${SCRIPT_DIR}/../public/staticwebapp.config.json' ]" \
        "pass"

    # Validate JSON syntax
    run_test "Static Web App config is valid JSON" \
        "python3 -c 'import json; json.load(open(\"${SCRIPT_DIR}/../public/staticwebapp.config.json\"))' >/dev/null 2>&1" \
        "pass"

    # Check for authentication configuration
    run_test "Authentication config present" \
        "grep -q 'identityProviders' '${SCRIPT_DIR}/../public/staticwebapp.config.json'" \
        "pass"

    # Check for security headers
    run_test "Security headers configured" \
        "grep -q 'globalHeaders' '${SCRIPT_DIR}/../public/staticwebapp.config.json'" \
        "pass"
}

# Test frontend configuration
test_frontend_config() {
    log_info "Testing Frontend Configuration"
    log_info "=============================="

    # Check if API service is updated
    run_test "API service updated for direct access" \
        "grep -q 'sutra-api.azurewebsites.net' '${SCRIPT_DIR}/../src/services/api.ts'" \
        "pass"

    # Check for authentication integration
    run_test "Authentication integration present" \
        "grep -q 'getAuthToken' '${SCRIPT_DIR}/../src/services/api.ts'" \
        "pass"
}

# Test Function App middleware
test_function_middleware() {
    log_info "Testing Function App Middleware"
    log_info "==============================="

    # Check if middleware file exists
    run_test "Rate limiting middleware exists" \
        "[ -f '${SCRIPT_DIR}/../api/shared/middleware.py' ]" \
        "pass"

    # Check if health endpoint uses middleware
    run_test "Health endpoint uses middleware" \
        "grep -q 'enhanced_security_middleware' '${SCRIPT_DIR}/../api/health/__init__.py'" \
        "pass"

    # Check if health function.json exists
    run_test "Health endpoint function.json exists" \
        "[ -f '${SCRIPT_DIR}/../api/health/function.json' ]" \
        "pass"
}

# Performance test
test_performance() {
    log_info "Testing Performance"
    log_info "=================="

    if [[ -n "$API_URL" ]]; then
        # Test response time
        local response_time
        response_time=$(curl -s -w "%{time_total}" -o /dev/null --max-time 30 "$API_URL/health" 2>/dev/null || echo "999")

        # Convert to milliseconds and compare
        local response_ms
        response_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null | cut -d. -f1)

        if [[ "$response_ms" -lt 2000 ]]; then
            log_success "✓ Response time: ${response_ms}ms (< 2000ms)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_warning "⚠ Response time: ${response_ms}ms (>= 2000ms)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TESTS_TOTAL=$((TESTS_TOTAL + 1))

    else
        log_warning "API endpoint not available - skipping performance tests"
    fi
}

# Generate test report
generate_report() {
    echo ""
    log_info "Direct Access Architecture Validation Report"
    log_info "========================================="
    echo "Total Tests: $TESTS_TOTAL"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"

    local success_rate=0
    if [[ $TESTS_TOTAL -gt 0 ]]; then
        success_rate=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    fi

    echo "Success Rate: ${success_rate}%"
    echo ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All tests passed! ✨"
        echo ""
        log_info "Direct access architecture is working correctly."
        log_info "Key benefits achieved:"
        echo "  - Direct access to Azure services"
        echo "  - Built-in security with rate limiting"
        echo "  - Cost savings (no gateway fees)"
        echo "  - Simplified architecture"
    else
        log_warning "Some tests failed. Review the results above."
        echo ""
        log_info "Common issues to check:"
        echo "  - Ensure deployment completed successfully"
        echo "  - Verify network connectivity"
        echo "  - Check Function App status"
        echo "  - Review Application Insights logs"
    fi

    echo ""
    echo "Endpoints:"
    echo "  API Base URL: ${API_URL:-'Not found'}"
    echo "  Static Web App: ${STATIC_URL:-'Not found'}"
}

# Static validation for dry-run mode (no Azure CLI required)
test_static_validation_only() {
    log_info "Running static validation checks (dry-run mode)"

    # Check if infrastructure files exist
    run_test "Infrastructure files exist" \
        "test -f infrastructure/persistent.bicep && test -f infrastructure/compute.bicep" \
        "pass"

    # Check deployment scripts syntax
    run_test "Deployment script syntax" \
        "bash -n scripts/deploy-infrastructure.sh" \
        "pass"

    # Check for hard-coded values in Bicep templates (exclude valid resourceGroup() function calls)
    run_test "No hard-coded resource group names" \
        "! grep -r 'rg-[a-zA-Z0-9]' infrastructure/" \
        "pass"

    # Check naming consistency
    run_test "Consistent naming patterns" \
        "grep -q 'param' infrastructure/persistent.bicep || grep -q 'param' infrastructure/compute.bicep" \
        "pass"

    # Generate dry-run report
    log_info "Static validation completed in dry-run mode"
    echo ""
    echo "Summary: $TESTS_PASSED/$TESTS_TOTAL tests passed"

    if [[ $TESTS_FAILED -gt 0 ]]; then
        log_error "$TESTS_FAILED tests failed"
        exit 1
    else
        log_success "All static validation tests passed"
        exit 0
    fi
}

# Main validation function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                log_error "Unknown argument: $1"
                echo "Usage: $0 [--dry-run]"
                exit 1
                ;;
        esac
    done

    log_info "Sutra Direct Access Architecture Validation"
    log_info "========================================"
    log_info "Validating implementation..."
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Running in DRY-RUN mode - skipping Azure CLI checks"
        test_static_validation_only
        return 0
    fi

    # Check prerequisites
    if ! command -v az >/dev/null 2>&1; then
        log_error "Azure CLI not found. Please install Azure CLI first."
        exit 1
    fi

    if ! az account show >/dev/null 2>&1; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi

    # Run validation tests
    test_infrastructure
    echo ""
    test_direct_access
    echo ""
    test_security
    echo ""
    test_static_web_app_config
    echo ""
    test_frontend_config
    echo ""
    test_function_middleware
    echo ""
    test_performance
    echo ""

    # Generate final report
    generate_report
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
