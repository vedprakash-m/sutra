#!/bin/bash

# No-Gateway Architecture Validation Script for Sutra
# Validates direct Azure Functions access without API Management Gateway
# Architecture: Static Web App + Azure Functions (Direct Access)

set -e

echo "🔍 Sutra No-Gateway Architecture Validation"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ISSUES_FOUND=0
START_TIME=$(date +%s)

# Helper functions
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; ((ISSUES_FOUND++)); }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites for no-gateway architecture..."

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not installed"
        return 1
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure CLI"
        log_info "Run: az login"
        return 1
    fi

    # Check required files
    if [ ! -f "infrastructure/compute-no-gateway.bicep" ]; then
        log_error "No-gateway Bicep template not found"
        return 1
    fi

    if [ ! -f "infrastructure/persistent.bicep" ]; then
        log_error "Persistent infrastructure template not found"
        return 1
    fi

    log_success "Prerequisites check passed"
    return 0
}

# Validate Bicep templates
validate_bicep_templates() {
    log_info "Validating Bicep templates for no-gateway architecture..."

    # Validate persistent infrastructure template
    if az bicep build --file infrastructure/persistent.bicep --stdout > /dev/null; then
        log_success "Persistent infrastructure template is valid"
    else
        log_error "Persistent infrastructure template validation failed"
    fi

    # Validate compute-no-gateway template
    if [ -s "infrastructure/compute-no-gateway.bicep" ]; then
        if az bicep build --file infrastructure/compute-no-gateway.bicep --stdout > /dev/null; then
            log_success "No-gateway compute template is valid"
        else
            log_error "No-gateway compute template validation failed"
        fi
    else
        log_warning "No-gateway compute template is empty - needs implementation"
        ((ISSUES_FOUND++))
    fi
}

# Validate no-gateway specific configurations
validate_no_gateway_config() {
    log_info "Validating no-gateway architecture configurations..."

    # Check frontend API configuration for direct Azure Functions access
    if [ -f "src/services/api.ts" ]; then
        if grep -q "azure.*functions" src/services/api.ts; then
            log_success "Frontend configured for Azure Functions direct access"
        else
            log_warning "Frontend may not be configured for direct Azure Functions access"
        fi
    fi

    # Check CORS configuration in function app
    if [ -f "infrastructure/compute.bicep" ]; then
        if grep -A 10 "cors:" infrastructure/compute.bicep | grep -q "allowedOrigins"; then
            log_success "CORS configuration found in Azure Functions"
        else
            log_warning "CORS configuration may be missing"
        fi
    fi

    # Check security configurations
    if [ -f "infrastructure/compute.bicep" ]; then
        if grep -q "httpsOnly.*true" infrastructure/compute.bicep; then
            log_success "HTTPS-only configuration enabled"
        else
            log_error "HTTPS-only configuration missing"
        fi

        if grep -q "minTlsVersion.*1.2" infrastructure/compute.bicep; then
            log_success "Minimum TLS 1.2 configured"
        else
            log_warning "Minimum TLS version not explicitly set"
        fi
    fi
}

# Validate Static Web App configuration
validate_static_web_app() {
    log_info "Validating Static Web App configuration..."

    # Check static web app config
    if [ -f "public/staticwebapp.config.json" ]; then
        log_success "Static Web App configuration file exists"

        # Validate JSON syntax
        if jq empty public/staticwebapp.config.json 2>/dev/null; then
            log_success "Static Web App config JSON is valid"
        else
            log_error "Static Web App config JSON is invalid"
        fi

        # Check routing configuration
        if jq -e '.routes' public/staticwebapp.config.json > /dev/null; then
            log_success "Routing configuration found"
        else
            log_warning "No routing configuration in static web app config"
        fi

        # Check API configuration for Azure Functions
        if jq -e '.apiLocation' public/staticwebapp.config.json > /dev/null; then
            api_location=$(jq -r '.apiLocation' public/staticwebapp.config.json)
            log_success "API location configured: $api_location"
        else
            log_warning "API location not configured in static web app"
        fi
    else
        log_error "Static Web App configuration file missing"
    fi
}

# Validate authentication configuration
validate_authentication() {
    log_info "Validating authentication for no-gateway architecture..."

    # Check auth configuration in static web app
    if [ -f "public/staticwebapp.config.json" ]; then
        if jq -e '.auth' public/staticwebapp.config.json > /dev/null; then
            log_success "Authentication configuration found"

            # Check auth providers
            if jq -e '.auth.identityProviders' public/staticwebapp.config.json > /dev/null; then
                log_success "Identity providers configured"
            else
                log_warning "No identity providers configured"
            fi
        else
            log_warning "No authentication configuration in static web app"
        fi
    fi

    # Check function app auth
    if [ -f "api/shared/auth.py" ]; then
        if grep -q "azure.*identity" api/shared/auth.py; then
            log_success "Azure identity integration in backend"
        else
            log_warning "Azure identity integration may be missing"
        fi
    fi
}

# Validate deployment configurations
validate_deployment_config() {
    log_info "Validating deployment configuration for no-gateway..."

    # Check if deployment parameters exist
    if [ -f "infrastructure/parameters.compute-no-gateway.json" ]; then
        log_success "No-gateway deployment parameters exist"

        # Validate JSON
        if jq empty infrastructure/parameters.compute-no-gateway.json 2>/dev/null; then
            log_success "Deployment parameters JSON is valid"
        else
            log_error "Deployment parameters JSON is invalid"
        fi
    else
        log_warning "No-gateway deployment parameters missing"
    fi

    # Check GitHub Actions workflow for no-gateway deployment
    if [ -f ".github/workflows/deploy-no-gateway.yml" ]; then
        log_success "No-gateway deployment workflow exists"
    else
        log_warning "No-gateway deployment workflow missing"
    fi
}

# Validate environment-specific configurations
validate_environment_config() {
    log_info "Validating environment configuration..."

    # Check environment variables setup
    local env_vars=(
        "FUNCTIONS_WORKER_RUNTIME"
        "APPINSIGHTS_INSTRUMENTATIONKEY"
        "COSMOS_DB_CONNECTION_STRING"
        "SUTRA_ENVIRONMENT"
    )

    if [ -f "infrastructure/compute.bicep" ]; then
        for var in "${env_vars[@]}"; do
            if grep -q "$var" infrastructure/compute.bicep; then
                log_success "Environment variable $var configured"
            else
                log_warning "Environment variable $var missing"
            fi
        done
    fi
}

# Validate security configurations specific to no-gateway
validate_security() {
    log_info "Validating security for no-gateway architecture..."

    # Check rate limiting
    if [ -f "api/shared/middleware.py" ]; then
        if grep -q "rate.*limit" api/shared/middleware.py; then
            log_success "Rate limiting implemented in middleware"
        else
            log_warning "Rate limiting may not be implemented"
        fi
    fi

    # Check input validation
    if [ -f "api/shared/validation.py" ]; then
        if grep -q "sanitize\|validate" api/shared/validation.py; then
            log_success "Input validation implemented"
        else
            log_warning "Input validation may be insufficient"
        fi
    fi

    # Check error handling
    if [ -f "api/shared/error_handling.py" ]; then
        if grep -q "sanitize_error_message" api/shared/error_handling.py; then
            log_success "Error message sanitization implemented"
        else
            log_warning "Error message sanitization missing"
        fi
    fi
}

# Validate build and deployment readiness
validate_build_readiness() {
    log_info "Validating build and deployment readiness..."

    # Check frontend build
    if [ -f "package.json" ]; then
        if npm run build > /tmp/build.log 2>&1; then
            log_success "Frontend builds successfully"
        else
            log_error "Frontend build failed"
            echo "Build error details:"
            tail -10 /tmp/build.log
        fi
    fi

    # Check backend package requirements
    if [ -f "api/requirements.txt" ]; then
        log_success "Backend requirements file exists"
    else
        log_error "Backend requirements file missing"
    fi

    # Check function.json files
    local function_count=$(find api -name "function.json" | wc -l)
    if [ "$function_count" -gt 0 ]; then
        log_success "Found $function_count Azure Functions"
    else
        log_error "No Azure Function definitions found"
    fi
}

# Main validation flow
main() {
    echo "Starting no-gateway architecture validation..."
    echo ""

    check_prerequisites || exit 1
    validate_bicep_templates
    validate_no_gateway_config
    validate_static_web_app
    validate_authentication
    validate_deployment_config
    validate_environment_config
    validate_security
    validate_build_readiness

    echo ""
    echo "Validation Summary:"
    echo "=================="

    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    if [ $ISSUES_FOUND -eq 0 ]; then
        log_success "No-gateway architecture validation completed successfully! (${duration}s)"
        echo ""
        echo "🚀 Ready for no-gateway deployment!"
        echo ""
        echo "Next steps:"
        echo "1. Deploy persistent infrastructure: ./scripts/deploy-infrastructure.sh"
        echo "2. Deploy no-gateway compute: ./scripts/deploy-no-gateway.sh"
        echo "3. Run E2E tests: npm run test:e2e"
        exit 0
    else
        log_error "No-gateway architecture validation failed with $ISSUES_FOUND issues (${duration}s)"
        echo ""
        echo "🔧 Please fix the issues above before deployment."
        exit 1
    fi
}

# Run validation
main "$@"
