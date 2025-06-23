#!/bin/bash

# Comprehensive Authentication Testing Script
# Tests all aspects of Entra External ID integration with Azure Static Web Apps

set -e

echo "🔐 COMPREHENSIVE AUTHENTICATION TESTING"
echo "======================================="
echo ""

# Configuration from metadata
FRONTEND_URL="https://salmon-pond-004adb91e.1.azurestaticapps.net"
API_URL="https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api"
LOCAL_DEV_URL="http://localhost:5173"

# Color output functions
log_info() { echo -e "\033[36mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[32m✅ $1\033[0m"; }
log_warning() { echo -e "\033[33m⚠️  $1\033[0m"; }
log_error() { echo -e "\033[31m❌ $1\033[0m"; }

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

# Test function helper
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="$3"

    ((TOTAL_TESTS++))
    echo "🧪 Test $TOTAL_TESTS: $test_name"
    echo "   Command: $test_command"

    # Execute test
    if eval "$test_command"; then
        if [[ -n "$expected_status" ]]; then
            # Check specific status code if provided
            actual_status=$(eval "$test_command" 2>/dev/null | grep -o "[0-9][0-9][0-9]" | head -1)
            if [[ "$actual_status" == "$expected_status" ]]; then
                log_success "   PASSED (Status: $actual_status)"
                ((PASSED_TESTS++))
            else
                log_warning "   FAILED (Expected: $expected_status, Got: $actual_status)"
            fi
        else
            log_success "   PASSED"
            ((PASSED_TESTS++))
        fi
    else
        log_error "   FAILED"
    fi
    echo ""
}

# Test 1: Static Web App Configuration
test_static_web_app_config() {
    log_info "📋 Testing Static Web App Configuration"
    echo "========================================"

    # Check staticwebapp.config.json
    if [[ -f "public/staticwebapp.config.json" ]]; then
        log_success "staticwebapp.config.json found"

        # Validate Entra External ID configuration
        if grep -q "login.microsoftonline.com" "public/staticwebapp.config.json"; then
            log_success "Entra External ID endpoint configured"
        else
            log_error "Entra External ID endpoint not found (should be login.microsoftonline.com)"
        fi

        # Check roles source
        if grep -q '"/api/getroles"' "public/staticwebapp.config.json"; then
            log_success "Roles source endpoint configured"
        else
            log_error "Roles source endpoint not configured"
        fi
    else
        log_error "staticwebapp.config.json not found"
    fi

    echo ""
}

# Test 2: Authentication Endpoints
test_auth_endpoints() {
    log_info "🌐 Testing Authentication Endpoints"
    echo "===================================="

    # Test /.auth/me endpoint
    run_test "Auth Me Endpoint" \
        "curl -s -o /dev/null -w '%{http_code}' '$FRONTEND_URL/.auth/me'" \
        "200|401"

    # Test /.auth/providers endpoint
    run_test "Auth Providers Endpoint" \
        "curl -s -o /dev/null -w '%{http_code}' '$FRONTEND_URL/.auth/providers'" \
        "200"

    # Test login redirect
    run_test "Auth Login Redirect" \
        "curl -s -o /dev/null -w '%{http_code}' '$FRONTEND_URL/.auth/login/azureActiveDirectory'" \
        "302"

    echo ""
}

# Test 3: API Authentication
test_api_authentication() {
    log_info "🔌 Testing API Authentication"
    echo "=============================="

    # Test health endpoint (should be accessible)
    run_test "Health Endpoint (Public)" \
        "curl -s -o /dev/null -w '%{http_code}' '$API_URL/health'" \
        "200"

    # Test getroles endpoint (requires authentication)
    run_test "GetRoles Endpoint (Protected)" \
        "curl -s -o /dev/null -w '%{http_code}' '$API_URL/getroles'" \
        "401|403"

    # Test admin endpoint (requires admin role)
    run_test "Admin Endpoint (Admin Only)" \
        "curl -s -o /dev/null -w '%{http_code}' '$API_URL/admin_api'" \
        "401|403"

    echo ""
}

# Test 4: CORS Configuration
test_cors_configuration() {
    log_info "🌍 Testing CORS Configuration"
    echo "=============================="

    # Test CORS preflight
    run_test "CORS Preflight" \
        "curl -s -o /dev/null -w '%{http_code}' -X OPTIONS -H 'Origin: $FRONTEND_URL' '$API_URL/health'" \
        "200|204"

    # Test CORS with credentials
    cors_headers=$(curl -s -I -X OPTIONS \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: authorization" \
        "$API_URL/health" | grep -i "access-control")

    if echo "$cors_headers" | grep -q "access-control-allow-credentials.*true"; then
        log_success "   CORS credentials enabled"
        ((PASSED_TESTS++))
    else
        log_warning "   CORS credentials not properly configured"
    fi

    ((TOTAL_TESTS++))
    echo ""
}

# Test 5: Security Headers
test_security_headers() {
    log_info "🛡️  Testing Security Headers"
    echo "============================="

    # Get headers from Static Web App
    headers=$(curl -s -I "$FRONTEND_URL" | tr -d '\r')

    # Test Content Security Policy
    if echo "$headers" | grep -qi "content-security-policy"; then
        log_success "   Content Security Policy header present"
        ((PASSED_TESTS++))
    else
        log_warning "   Content Security Policy header missing"
    fi

    # Test X-Content-Type-Options
    if echo "$headers" | grep -qi "x-content-type-options.*nosniff"; then
        log_success "   X-Content-Type-Options header present"
        ((PASSED_TESTS++))
    else
        log_warning "   X-Content-Type-Options header missing"
    fi

    # Test X-Frame-Options
    if echo "$headers" | grep -qi "x-frame-options.*deny"; then
        log_success "   X-Frame-Options header present"
        ((PASSED_TESTS++))
    else
        log_warning "   X-Frame-Options header missing"
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 3))
    echo ""
}

# Test 6: Role Assignment Logic
test_role_assignment() {
    log_info "👤 Testing Role Assignment Logic"
    echo "================================="

    # Check if getroles endpoint exists and has proper structure
    if [[ -f "api/getroles/__init__.py" ]]; then
        log_success "   GetRoles endpoint implementation found"

        # Check for proper header handling
        if grep -q "x-ms-client-principal" "api/getroles/__init__.py"; then
            log_success "   Static Web Apps header parsing implemented"
            ((PASSED_TESTS++))
        else
            log_warning "   Static Web Apps header parsing not found"
        fi

        # Check for database integration
        if grep -q "get_database_manager" "api/getroles/__init__.py"; then
            log_success "   Database integration present"
            ((PASSED_TESTS++))
        else
            log_warning "   Database integration missing"
        fi

        ((PASSED_TESTS++))
    else
        log_error "   GetRoles endpoint implementation not found"
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 3))
    echo ""
}

# Test 7: Authentication Migration Status
test_auth_migration_status() {
    log_info "🔄 Testing Authentication Migration Status"
    echo "=========================================="

    # Check for new authentication manager
    if [[ -f "api/shared/auth_static_web_apps.py" ]]; then
        log_success "   New Static Web Apps auth manager found"
        ((PASSED_TESTS++))
    else
        log_error "   New Static Web Apps auth manager missing"
    fi

    # Check if endpoints are using new auth
    migrated_endpoints=0
    total_endpoints=0

    for endpoint in api/*/__init__.py; do
        if [[ "$endpoint" != "api/shared/__init__.py" && "$endpoint" != "api/__init__.py" ]]; then
            ((total_endpoints++))
            if grep -q "auth_static_web_apps" "$endpoint"; then
                ((migrated_endpoints++))
            fi
        fi
    done

    log_info "   Migration progress: $migrated_endpoints/$total_endpoints endpoints"

    if [[ $migrated_endpoints -eq $total_endpoints ]]; then
        log_success "   All endpoints migrated to new authentication"
        ((PASSED_TESTS++))
    elif [[ $migrated_endpoints -gt 0 ]]; then
        log_warning "   Partial migration completed"
    else
        log_error "   No endpoints migrated yet"
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 2))
    echo ""
}

# Test 8: Local Development Setup
test_local_development() {
    log_info "💻 Testing Local Development Setup"
    echo "==================================="

    # Check if local development can start
    if [[ -f "package.json" ]] && command -v npm &> /dev/null; then
        log_success "   Node.js environment available"
        ((PASSED_TESTS++))
    else
        log_warning "   Node.js environment not available"
    fi

    # Check for development auth fallback
    if grep -q "localStorage.*demo" "src/components/auth/AuthProvider.tsx"; then
        log_success "   Development auth fallback available"
        ((PASSED_TESTS++))
    else
        log_warning "   Development auth fallback not found"
    fi

    # Check local settings template
    if [[ -f "api/local.settings.json.example" ]]; then
        log_success "   Local settings template available"
        ((PASSED_TESTS++))
    else
        log_warning "   Local settings template missing"
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 3))
    echo ""
}

# Main test execution
main() {
    echo "Starting comprehensive authentication testing for Sutra application"
    echo "Frontend URL: $FRONTEND_URL"
    echo "API URL: $API_URL"
    echo ""

    test_static_web_app_config
    test_auth_endpoints
    test_api_authentication
    test_cors_configuration
    test_security_headers
    test_role_assignment
    test_auth_migration_status
    test_local_development

    # Final results
    echo "📊 TEST RESULTS"
    echo "==============="
    echo "Tests Passed: $PASSED_TESTS/$TOTAL_TESTS"
    echo ""

    if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
        log_success "🎉 ALL TESTS PASSED - Authentication is properly configured!"
    elif [[ $PASSED_TESTS -ge $((TOTAL_TESTS * 3 / 4)) ]]; then
        log_warning "🟡 MOSTLY CONFIGURED - Some minor issues to address"
    elif [[ $PASSED_TESTS -ge $((TOTAL_TESTS / 2)) ]]; then
        log_warning "🟠 PARTIALLY CONFIGURED - Several issues need attention"
    else
        log_error "🔴 CONFIGURATION INCOMPLETE - Major issues require immediate attention"
    fi

    echo ""
    echo "For detailed remediation steps, see:"
    echo "- docs/environment-variables.md"
    echo "- scripts/setup-static-web-app-auth.sh"
    echo "- scripts/migrate-authentication.sh"
}

# Run tests
main "$@"
