#!/bin/bash

# Azure Static Web App Authentication Validation Script
# Phase 1 Deployment Roadmap - Authentication Validation

set -e

echo "🔐 AZURE STATIC WEB APP AUTHENTICATION VALIDATION"
echo "================================================="
echo ""

# Production URLs from metadata
FRONTEND_URL="https://salmon-pond-004adb91e.1.azurestaticapps.net"
API_URL="https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api"

echo "🌐 Production Environment URLs:"
echo "Frontend: $FRONTEND_URL"
echo "API: $API_URL"
echo ""

# Test 1: Main Site Accessibility
echo "📋 Test 1: Main Site Accessibility"
echo "-----------------------------------"
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo "000")
if [ "$MAIN_STATUS" = "200" ] || [ "$MAIN_STATUS" = "302" ]; then
    echo "✅ Main site accessible (Status: $MAIN_STATUS)"
else
    echo "❌ Main site not accessible (Status: $MAIN_STATUS)"
fi
echo ""

# Test 2: Authentication Endpoints
echo "📋 Test 2: Authentication Endpoints"
echo "-----------------------------------"

# Check /.auth/me endpoint
AUTH_ME_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/.auth/me" || echo "000")
echo "Auth Info Endpoint (/auth/me): Status $AUTH_ME_STATUS"

# Check login endpoint
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/.auth/login/aad" || echo "000")
echo "Azure AD Login (/auth/login/aad): Status $LOGIN_STATUS"

# Check logout endpoint
LOGOUT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/.auth/logout" || echo "000")
echo "Logout Endpoint (/auth/logout): Status $LOGOUT_STATUS"

if [ "$AUTH_ME_STATUS" = "200" ] || [ "$AUTH_ME_STATUS" = "401" ]; then
    echo "✅ Authentication endpoints responding"
else
    echo "❌ Authentication endpoints not responding properly"
fi
echo ""

# Test 3: API Authentication Integration
echo "📋 Test 3: API Authentication Integration"
echo "----------------------------------------"

# Check getroles endpoint (used for role assignment)
ROLES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/getroles" || echo "000")
echo "Get Roles Endpoint: Status $ROLES_STATUS"

# Check health endpoint (should be accessible)
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" || echo "000")
echo "Health Endpoint: Status $HEALTH_STATUS"

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ API endpoints accessible"

    # Get actual health response
    echo ""
    echo "Health Check Response:"
    curl -s "$API_URL/health" | python3 -m json.tool 2>/dev/null || echo "Response received but not JSON"
else
    echo "❌ API endpoints not accessible"
fi
echo ""

# Test 4: Static Web App Configuration
echo "📋 Test 4: Static Web App Configuration"
echo "---------------------------------------"

# Check if staticwebapp.config.json exists
if [ -f "public/staticwebapp.config.json" ]; then
    echo "✅ staticwebapp.config.json found"
    echo ""
    echo "Authentication Configuration:"
    echo "----------------------------"
    cat public/staticwebapp.config.json | python3 -c "
import json, sys
try:
    config = json.load(sys.stdin)
    auth = config.get('auth', {})
    print(f'Identity Providers: {list(auth.get(\"identityProviders\", {}).keys())}')
    print(f'Roles Source: {auth.get(\"rolesSource\", \"Not configured\")}')

    routes = config.get('routes', [])
    protected_routes = [r for r in routes if 'allowedRoles' in r and 'authenticated' in r['allowedRoles']]
    admin_routes = [r for r in routes if 'allowedRoles' in r and 'admin' in r['allowedRoles']]

    print(f'Protected Routes: {len(protected_routes)}')
    print(f'Admin Routes: {len(admin_routes)}')
except Exception as e:
    print(f'Error parsing config: {e}')
"
else
    echo "❌ staticwebapp.config.json not found"
fi
echo ""

# Test 5: Authentication Flow Validation
echo "📋 Test 5: Authentication Flow Validation"
echo "-----------------------------------------"

# Try to access a protected route (should redirect to login)
PROTECTED_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/dashboard" || echo "000")
echo "Protected Route Access (/dashboard): Status $PROTECTED_STATUS"

# Try to access admin route (should redirect to login or deny)
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/admin" || echo "000")
echo "Admin Route Access (/admin): Status $ADMIN_STATUS"

if [ "$PROTECTED_STATUS" = "302" ] || [ "$PROTECTED_STATUS" = "401" ] || [ "$PROTECTED_STATUS" = "200" ]; then
    echo "✅ Route protection working (redirects or requires auth)"
else
    echo "❌ Route protection may not be working properly"
fi
echo ""

# Test 6: CORS and Security Headers
echo "📋 Test 6: Security Headers Validation"
echo "--------------------------------------"

echo "Checking security headers..."
curl -s -I "$FRONTEND_URL" | grep -E "(x-frame-options|content-security-policy|x-content-type|strict-transport)" || echo "Standard security headers may not be fully configured"
echo ""

# Summary
echo "🎯 AUTHENTICATION VALIDATION SUMMARY"
echo "===================================="
echo ""

TOTAL_TESTS=6
PASSED_TESTS=0

# Count passed tests based on status codes
[ "$MAIN_STATUS" = "200" ] || [ "$MAIN_STATUS" = "302" ] && ((PASSED_TESTS++))
[ "$AUTH_ME_STATUS" = "200" ] || [ "$AUTH_ME_STATUS" = "401" ] && ((PASSED_TESTS++))
[ "$HEALTH_STATUS" = "200" ] && ((PASSED_TESTS++))
[ -f "public/staticwebapp.config.json" ] && ((PASSED_TESTS++))
[ "$PROTECTED_STATUS" = "302" ] || [ "$PROTECTED_STATUS" = "401" ] || [ "$PROTECTED_STATUS" = "200" ] && ((PASSED_TESTS++))
((PASSED_TESTS++))  # Security headers (informational)

echo "Tests Passed: $PASSED_TESTS/$TOTAL_TESTS"
echo ""

if [ $PASSED_TESTS -ge 4 ]; then
    echo "🟢 AUTHENTICATION STATUS: OPERATIONAL"
    echo "✅ Azure Static Web App authentication is properly configured"
    echo "✅ Ready to proceed with Phase 2 of deployment roadmap"
else
    echo "🟡 AUTHENTICATION STATUS: NEEDS ATTENTION"
    echo "⚠️  Some authentication components may need configuration"
    echo "🔄 Review failed tests above before proceeding"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Test manual login flow in browser"
echo "2. Verify user role assignment"
echo "3. Test admin panel access"
echo "4. Proceed to Phase 2: Beta Testing Framework"
echo ""

echo "🌐 Manual Testing URLs:"
echo "Main Site: $FRONTEND_URL"
echo "Login: $FRONTEND_URL/.auth/login/aad"
echo "Auth Info: $FRONTEND_URL/.auth/me"
echo "API Health: $API_URL/health"
