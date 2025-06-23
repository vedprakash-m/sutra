#!/bin/bash

# COMPREHENSIVE AUTHENTICATION E2E TESTING
# Tests entire authentication flow from login to API access

set -e

echo "🧪 COMPREHENSIVE AUTHENTICATION E2E TESTING"
echo "============================================"
echo ""

# URLs
FRONTEND_URL="https://salmon-pond-004adb91e.1.azurestaticapps.net"
API_URL="https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
declare -a FAILED_TEST_DETAILS=()

log_test_start() {
    ((TOTAL_TESTS++))
    echo -e "${BLUE}🧪 Test $TOTAL_TESTS: $1${NC}"
}

log_test_pass() {
    ((PASSED_TESTS++))
    echo -e "${GREEN}  ✅ PASSED: $1${NC}"
}

log_test_fail() {
    ((FAILED_TESTS++))
    echo -e "${RED}  ❌ FAILED: $1${NC}"
    FAILED_TEST_DETAILS+=("Test $TOTAL_TESTS: $1")
}

log_test_warning() {
    echo -e "${YELLOW}  ⚠️  WARNING: $1${NC}"
}

# Test 1: Static Web App Configuration
test_static_web_app_config() {
    echo -e "${BLUE}📋 Phase 1: Static Web App Configuration${NC}"
    echo "========================================"

    log_test_start "staticwebapp.config.json exists and valid"
    if [[ -f "public/staticwebapp.config.json" ]]; then
        # Check for Entra External ID configuration
        if grep -q "login.microsoftonline.com" "public/staticwebapp.config.json"; then
            log_test_pass "Entra External ID endpoint configured"
        else
            log_test_fail "Entra External ID endpoint not found"
        fi

        # Check roles source
        if grep -q '"/api/getroles"' "public/staticwebapp.config.json"; then
            log_test_pass "Roles source endpoint configured"
        else
            log_test_fail "Roles source endpoint missing"
        fi
    else
        log_test_fail "staticwebapp.config.json not found"
    fi
    echo ""
}

# Test 2: Authentication Infrastructure
test_auth_infrastructure() {
    echo -e "${BLUE}🏗️ Phase 2: Authentication Infrastructure${NC}"
    echo "========================================="

    log_test_start "Azure Static Web Apps authentication endpoints"

    # Test /.auth/me
    auth_me_status=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/.auth/me" || echo "000")
    if [[ "$auth_me_status" == "200" || "$auth_me_status" == "401" ]]; then
        log_test_pass "/.auth/me endpoint active (Status: $auth_me_status)"
    else
        log_test_fail "/.auth/me endpoint not configured (Status: $auth_me_status)"
    fi

    # Test /.auth/providers
    auth_providers_status=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/.auth/providers" || echo "000")
    if [[ "$auth_providers_status" == "200" ]]; then
        log_test_pass "/.auth/providers endpoint active"

        # Check available providers
        providers=$(curl -s "$FRONTEND_URL/.auth/providers" 2>/dev/null)
        if echo "$providers" | grep -q "azureActiveDirectory\|microsoft"; then
            log_test_pass "Microsoft/Azure AD provider configured"
        else
            log_test_warning "Microsoft provider may not be configured"
        fi
    else
        log_test_fail "/.auth/providers endpoint not accessible (Status: $auth_providers_status)"
    fi

    # Test login redirect
    auth_login_status=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/.auth/login/azureActiveDirectory" || echo "000")
    if [[ "$auth_login_status" == "302" ]]; then
        log_test_pass "Authentication login redirect working"
    else
        log_test_fail "Authentication login redirect not working (Status: $auth_login_status)"
    fi

    echo ""
}

# Test 3: API Authentication
test_api_authentication() {
    echo -e "${BLUE}🔌 Phase 3: API Authentication${NC}"
    echo "================================"

    # Test health endpoint (should be public)
    log_test_start "Health endpoint accessibility"
    health_status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" || echo "000")
    if [[ "$health_status" == "200" ]]; then
        log_test_pass "Health endpoint accessible"
    else
        log_test_fail "Health endpoint not accessible (Status: $health_status)"
    fi

    # Test getroles endpoint (should require auth)
    log_test_start "GetRoles endpoint authentication"
    getroles_status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/getroles" || echo "000")
    if [[ "$getroles_status" == "401" || "$getroles_status" == "403" ]]; then
        log_test_pass "GetRoles endpoint properly protected"
    elif [[ "$getroles_status" == "404" ]]; then
        log_test_fail "GetRoles endpoint not deployed"
    else
        log_test_warning "GetRoles endpoint returned unexpected status: $getroles_status"
    fi

    # Test other API endpoints
    for endpoint in "collections_api" "prompts" "admin_api"; do
        log_test_start "$endpoint authentication protection"
        endpoint_status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/$endpoint" || echo "000")
        if [[ "$endpoint_status" == "401" || "$endpoint_status" == "403" ]]; then
            log_test_pass "$endpoint properly protected"
        elif [[ "$endpoint_status" == "404" ]]; then
            log_test_fail "$endpoint not deployed"
        else
            log_test_warning "$endpoint returned unexpected status: $endpoint_status"
        fi
    done

    echo ""
}

# Test 4: Code Migration Status
test_code_migration() {
    echo -e "${BLUE}🔄 Phase 4: Code Migration Status${NC}"
    echo "=================================="

    log_test_start "Authentication manager implementation"
    if [[ -f "api/shared/auth_static_web_apps.py" ]]; then
        log_test_pass "New authentication manager exists"
    else
        log_test_fail "New authentication manager missing"
    fi

    # Check endpoint migration status
    migrated_count=0
    total_endpoints=0

    for endpoint in api/*/; do
        endpoint_name=$(basename "$endpoint")
        if [[ "$endpoint_name" != "shared" && -f "$endpoint/__init__.py" ]]; then
            ((total_endpoints++))
            if grep -q "auth_static_web_apps" "$endpoint/__init__.py"; then
                ((migrated_count++))
                log_test_pass "$endpoint_name migrated to new auth"
            else
                log_test_fail "$endpoint_name still uses legacy auth"
            fi
        fi
    done

    log_test_start "Overall migration progress"
    if [[ $migrated_count -eq $total_endpoints ]]; then
        log_test_pass "All endpoints migrated ($migrated_count/$total_endpoints)"
    else
        log_test_fail "Migration incomplete ($migrated_count/$total_endpoints endpoints)"
    fi

    echo ""
}

# Test 5: Security Validation
test_security() {
    echo -e "${BLUE}🛡️ Phase 5: Security Validation${NC}"
    echo "================================="

    # Check for legacy JWT usage
    log_test_start "Legacy JWT authentication removal"
    if grep -r "verify_signature.*False" api/ 2>/dev/null; then
        log_test_fail "Insecure JWT validation found in code"
    else
        log_test_pass "No insecure JWT validation found"
    fi

    # Check for mock tokens in production code
    log_test_start "Production security (no mock tokens)"
    if grep -r "mock.*token\|dev.*token" api/ --exclude-dir=shared --exclude="*test*" 2>/dev/null; then
        log_test_fail "Mock/dev tokens found in production code"
    else
        log_test_pass "No mock tokens in production code"
    fi

    # Check CORS configuration
    log_test_start "CORS security headers"
    cors_headers=$(curl -s -I -X OPTIONS \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: GET" \
        "$API_URL/health" 2>/dev/null | grep -i "access-control" || echo "")

    if echo "$cors_headers" | grep -q "access-control-allow-origin"; then
        log_test_pass "CORS headers present"
    else
        log_test_fail "CORS headers missing"
    fi

    # Check security headers on frontend
    log_test_start "Frontend security headers"
    security_headers=$(curl -s -I "$FRONTEND_URL" | grep -i "content-security-policy\|x-frame-options\|x-content-type-options" || echo "")
    if [[ -n "$security_headers" ]]; then
        log_test_pass "Security headers present"
    else
        log_test_warning "Security headers may be missing"
    fi

    echo ""
}

# Test 6: User Experience Flow
test_user_experience() {
    echo -e "${BLUE}👤 Phase 6: User Experience Flow${NC}"
    echo "================================="

    log_test_start "Frontend loads successfully"
    frontend_status=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo "000")
    if [[ "$frontend_status" == "200" ]]; then
        log_test_pass "Frontend loads successfully"
    else
        log_test_fail "Frontend not loading (Status: $frontend_status)"
    fi

    log_test_start "Authentication flow initiation"
    # Check if login page/flow is accessible
    if curl -s "$FRONTEND_URL" | grep -q "login\|sign.*in\|authenticate" 2>/dev/null; then
        log_test_pass "Authentication UI elements present"
    else
        log_test_warning "Authentication UI may not be properly configured"
    fi

    log_test_start "Role assignment logic"
    if [[ -f "api/getroles/__init__.py" ]]; then
        if grep -q "admin.*in.*name\|name.*admin" "api/getroles/__init__.py"; then
            log_test_pass "Admin role assignment logic implemented"
        else
            log_test_warning "Admin role assignment may need configuration"
        fi
    else
        log_test_fail "Role assignment endpoint missing"
    fi

    echo ""
}

# Generate final report
generate_report() {
    echo -e "${BLUE}📊 FINAL AUTHENTICATION ASSESSMENT${NC}"
    echo "===================================="
    echo ""
    echo "Tests Run: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo ""

    # Calculate percentage
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        percentage=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    else
        percentage=0
    fi

    # Determine overall status
    if [[ $percentage -ge 90 ]]; then
        echo -e "${GREEN}🎉 AUTHENTICATION STATUS: EXCELLENT ($percentage%)${NC}"
        echo "✅ Authentication system is production-ready"
    elif [[ $percentage -ge 70 ]]; then
        echo -e "${YELLOW}⚠️  AUTHENTICATION STATUS: GOOD ($percentage%)${NC}"
        echo "🔧 Minor issues need attention"
    elif [[ $percentage -ge 50 ]]; then
        echo -e "${YELLOW}🟡 AUTHENTICATION STATUS: NEEDS WORK ($percentage%)${NC}"
        echo "🔨 Several issues require fixing"
    else
        echo -e "${RED}🚨 AUTHENTICATION STATUS: CRITICAL ISSUES ($percentage%)${NC}"
        echo "💥 Major problems need immediate attention"
    fi

    # Show failed tests
    if [[ ${#FAILED_TEST_DETAILS[@]} -gt 0 ]]; then
        echo ""
        echo -e "${RED}❌ FAILED TESTS REQUIRING ATTENTION:${NC}"
        for detail in "${FAILED_TEST_DETAILS[@]}"; do
            echo -e "${RED}  • $detail${NC}"
        done
    fi

    echo ""
    echo -e "${BLUE}🔧 NEXT STEPS:${NC}"
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo "• All tests passed! Authentication system is ready"
        echo "• Monitor authentication metrics in production"
        echo "• Consider adding more comprehensive e2e tests"
    else
        echo "• Run emergency fix: ./scripts/emergency-auth-fix.sh"
        echo "• Enable authentication in Azure Portal"
        echo "• Deploy updated API endpoints"
        echo "• Re-run this test after fixes"
    fi

    echo ""
    echo -e "${BLUE}📞 SUPPORT RESOURCES:${NC}"
    echo "• Implementation Guide: docs/authentication-implementation-guide.md"
    echo "• Emergency Fix Script: scripts/emergency-auth-fix.sh"
    echo "• Environment Setup: docs/environment-variables.md"
}

# Main execution
main() {
    echo "This script performs comprehensive end-to-end authentication testing"
    echo "for the Sutra application's Microsoft Entra External ID integration."
    echo ""
    echo "Testing environment:"
    echo "Frontend: $FRONTEND_URL"
    echo "API: $API_URL"
    echo ""

    test_static_web_app_config
    test_auth_infrastructure
    test_api_authentication
    test_code_migration
    test_security
    test_user_experience
    generate_report
}

# Run all tests
main "$@"
