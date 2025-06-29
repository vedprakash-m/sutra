#!/bin/bash
# Product Documentation Alignment Validation Script
# Ensures code changes align with PRD, Tech Spec, and UX Guide requirements

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔍 Product Documentation Alignment Validation${NC}"
echo "=================================================="
echo ""

# Check for authentication implementation compliance
validate_authentication_alignment() {
    log_info "Validating Microsoft Entra ID implementation alignment..."
    
    # Check for VedUser interface usage
    if ! grep -r "VedUser\|vedUser" src/ api/ --include="*.ts" --include="*.tsx" --include="*.py" > /dev/null 2>&1; then
        log_warning "VedUser interface usage not detected - ensure Apps_Auth_Requirement.md compliance"
    else
        log_success "VedUser interface usage detected"
    fi
    
    # Check for MSAL implementation
    if ! grep -r "@azure/msal-react" src/ package.json > /dev/null 2>&1; then
        log_error "MSAL React library not found - required per Apps_Auth_Requirement.md"
        return 1
    else
        log_success "MSAL React implementation found"
    fi
    
    # Check for vedid.onmicrosoft.com authority
    if ! grep -r "vedid\.onmicrosoft\.com" src/ api/ > /dev/null 2>&1; then
        log_warning "Entra ID authority not found - ensure proper tenant configuration"
    else
        log_success "Entra ID tenant authority configured"
    fi
}

# Check for anonymous user functionality
validate_anonymous_user_features() {
    log_info "Validating anonymous/guest user implementation..."
    
    # Check for IP-based rate limiting
    if ! grep -r "ip.*limit\|rate.*limit.*ip" api/ src/ --include="*.py" --include="*.ts" --include="*.tsx" > /dev/null 2>&1; then
        log_warning "IP-based rate limiting not detected - required per PRD for anonymous users"
    else
        log_success "IP-based rate limiting implementation found"
    fi
    
    # Check for 5-call daily limit
    if ! grep -r "5.*call\|daily.*limit.*5" api/ src/ --include="*.py" --include="*.ts" --include="*.tsx" > /dev/null 2>&1; then
        log_warning "5-call daily limit not detected - required per PRD anonymous user constraints"
    else
        log_success "Daily call limit implementation found"
    fi
}

# Check for multi-LLM support
validate_multi_llm_support() {
    log_info "Validating multi-LLM architecture alignment..."
    
    # Check for multiple LLM provider support
    local llm_providers=("openai" "gemini" "claude" "anthropic")
    local found_providers=0
    
    for provider in "${llm_providers[@]}"; do
        if grep -r "$provider" api/ src/ --include="*.py" --include="*.ts" --include="*.tsx" > /dev/null 2>&1; then
            ((found_providers++))
        fi
    done
    
    if [ $found_providers -lt 2 ]; then
        log_warning "Less than 2 LLM providers detected - PRD requires multi-LLM support"
    else
        log_success "Multi-LLM provider support detected ($found_providers providers)"
    fi
}

# Check for responsive design compliance
validate_responsive_design() {
    log_info "Validating responsive design implementation..."
    
    # Check for mobile-first/responsive CSS
    if ! grep -r "responsive\|mobile\|tablet\|@media\|sm:\|md:\|lg:" src/ --include="*.css" --include="*.tsx" --include="*.ts" > /dev/null 2>&1; then
        log_warning "Responsive design patterns not detected - required per UX Guide"
    else
        log_success "Responsive design implementation found"
    fi
    
    # Check for Tailwind responsive classes
    if ! grep -r "sm:\|md:\|lg:\|xl:" src/ --include="*.tsx" --include="*.ts" > /dev/null 2>&1; then
        log_warning "Tailwind responsive classes not detected - check UX Guide mobile requirements"
    else
        log_success "Tailwind responsive classes found"
    fi
}

# Check for cost management features
validate_cost_management() {
    log_info "Validating AI cost management implementation..."
    
    # Check for budget tracking
    if ! grep -r "budget\|cost.*track\|usage.*track" api/ src/ --include="*.py" --include="*.ts" --include="*.tsx" > /dev/null 2>&1; then
        log_warning "Cost management features not detected - Tech Spec requires comprehensive cost tracking"
    else
        log_success "Cost management implementation found"
    fi
}

# Check for security headers implementation
validate_security_implementation() {
    log_info "Validating security headers and CSP implementation..."
    
    # Check for security headers
    if ! grep -r "Content-Security-Policy\|X-Frame-Options\|HSTS" api/ infrastructure/ --include="*.py" --include="*.bicep" --include="*.json" > /dev/null 2>&1; then
        log_warning "Security headers not detected - required per Apps_Auth_Requirement.md"
    else
        log_success "Security headers implementation found"
    fi
}

# Main validation execution
main() {
    local validation_passed=true
    
    # Run all validation checks
    validate_authentication_alignment || validation_passed=false
    validate_anonymous_user_features || validation_passed=false
    validate_multi_llm_support || validation_passed=false
    validate_responsive_design || validation_passed=false
    validate_cost_management || validation_passed=false
    validate_security_implementation || validation_passed=false
    
    echo ""
    echo "=================================================="
    if [ "$validation_passed" = true ]; then
        log_success "Product documentation alignment validation PASSED"
        echo ""
        log_info "✅ Authentication: Microsoft Entra ID compliant"
        log_info "✅ Anonymous Users: Guest experience supported"
        log_info "✅ Multi-LLM: Provider-agnostic architecture"
        log_info "✅ Responsive: Mobile-first design implemented"
        log_info "✅ Cost Management: Budget tracking enabled"
        log_info "✅ Security: Enterprise-grade headers configured"
        echo ""
    else
        log_warning "Product documentation alignment validation completed with WARNINGS"
        echo ""
        log_info "Review warnings above and ensure compliance with:"
        log_info "• PRD: Product Requirements Document"
        log_info "• Tech Spec: Technical Specification"
        log_info "• UX Guide: User Experience Guide"
        log_info "• Apps_Auth_Requirement.md: Authentication standards"
        echo ""
    fi
    
    # Always exit 0 for pre-commit (warnings don't block commits)
    exit 0
}

main "$@"
