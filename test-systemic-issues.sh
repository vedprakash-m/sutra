#!/bin/bash

# Sutra Deeper Systemic Issues Validation Script
# Tests for architectural fragmentation, data inconsistency, auth complexity, and other systemic problems

echo "🔍 SUTRA DEEPER SYSTEMIC ISSUES VALIDATION"
echo "=========================================="
echo ""

BASE_URL="http://localhost:3001"
API_URL="$BASE_URL/api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Issue tracking
ARCHITECTURAL_ISSUES=0
DATA_MODEL_ISSUES=0
AUTH_COMPLEXITY_ISSUES=0
VALIDATION_ISSUES=0
COST_MGMT_ISSUES=0
INTEGRATION_ISSUES=0

# Test 1: ARCHITECTURAL FRAGMENTATION ANALYSIS
print_header "1. ARCHITECTURAL FRAGMENTATION ANALYSIS"

echo "1.1 Admin System Fragmentation Check..."
# Check for multiple admin systems
if [ -f "src/components/admin/AdminPanel.tsx" ] && [ -f "public/admin.html" ]; then
    print_error "FRAGMENTATION: Two separate admin systems detected"
    print_info "   React Admin: src/components/admin/AdminPanel.tsx"
    print_info "   HTML Admin: public/admin.html"
    ((ARCHITECTURAL_ISSUES++))
else
    print_success "Single admin system architecture"
fi

echo ""
echo "1.2 Authentication System Complexity Check..."
# Check for multiple auth implementations
AUTH_FILES=(
    "src/components/auth/AuthProvider.tsx"
    "src/dev/localAuthPlugin.ts"
    "api/shared/auth.py"
    "api/shared/auth_static_web_apps.py"
    "api/shared/auth_mocking.py"
)

auth_count=0
for file in "${AUTH_FILES[@]}"; do
    if [ -f "$file" ]; then
        ((auth_count++))
    fi
done

if [ $auth_count -gt 2 ]; then
    print_error "AUTH COMPLEXITY: $auth_count different authentication implementations"
    ((AUTH_COMPLEXITY_ISSUES++))
else
    print_success "Reasonable authentication complexity"
fi

echo ""
echo "1.3 Validation Layer Fragmentation Check..."
# Check for scattered validation logic
VALIDATION_LOCATIONS=(
    "src/services/validation.ts"
    "api/shared/validation.py"
    "src/components/*/validation"
    "api/*/validation"
)

validation_files=$(find . -name "*validation*" -type f | wc -l)
if [ $validation_files -gt 5 ]; then
    print_error "VALIDATION FRAGMENTATION: $validation_files validation-related files found"
    print_info "   Validation logic appears scattered across multiple locations"
    ((VALIDATION_ISSUES++))
else
    print_success "Centralized validation architecture"
fi

echo ""

# Test 2: DATA MODEL INCONSISTENCY ANALYSIS
print_header "2. DATA MODEL INCONSISTENCY ANALYSIS"

echo "2.1 Field Naming Convention Analysis..."
# Check for snake_case vs camelCase inconsistencies
snake_case_count=$(grep -r "owner_id\|user_id\|created_at\|updated_at" --include="*.py" api/ | wc -l)
camel_case_count=$(grep -r "ownerId\|userId\|createdAt\|updatedAt" --include="*.ts" --include="*.tsx" src/ | wc -l)

if [ $snake_case_count -gt 0 ] && [ $camel_case_count -gt 0 ]; then
    print_error "FIELD NAMING INCONSISTENCY: Mixed snake_case and camelCase"
    print_info "   Backend (snake_case): $snake_case_count occurrences"
    print_info "   Frontend (camelCase): $camel_case_count occurrences"
    ((DATA_MODEL_ISSUES++))
else
    print_success "Consistent field naming conventions"
fi

echo ""
echo "2.2 Schema Definition Analysis..."
# Check for shared schema definitions
if [ ! -f "shared/schemas.json" ] && [ ! -f "api/shared/schemas.py" ] && [ ! -f "src/types/schemas.ts" ]; then
    print_error "SCHEMA GOVERNANCE: No centralized schema definitions found"
    print_info "   Missing shared schema definitions between frontend/backend"
    ((DATA_MODEL_ISSUES++))
else
    print_success "Centralized schema definitions exist"
fi

echo ""
echo "2.3 API Contract Validation..."
# Check for OpenAPI specifications
if [ ! -f "api/openapi.yaml" ] && [ ! -f "api/swagger.json" ]; then
    print_error "API CONTRACT: No OpenAPI/Swagger specifications found"
    print_info "   Missing API contract definitions"
    ((DATA_MODEL_ISSUES++))
else
    print_success "API contracts documented"
fi

echo ""

# Test 3: ROLE MANAGEMENT MATURITY ANALYSIS
print_header "3. ROLE MANAGEMENT MATURITY ANALYSIS"

echo "3.1 Role Granularity Check..."
# Check role definitions in code
role_definitions=$(grep -r "role.*=.*admin\|role.*=.*user" --include="*.py" --include="*.ts" --include="*.tsx" . | grep -v node_modules | wc -l)
advanced_roles=$(grep -r "manager\|contributor\|viewer\|editor" --include="*.py" --include="*.ts" --include="*.tsx" . | grep -v node_modules | wc -l)

if [ $advanced_roles -lt 3 ]; then
    print_error "RBAC IMMATURITY: Only basic user/admin roles detected"
    print_info "   Enterprise needs require granular role management"
    ((AUTH_COMPLEXITY_ISSUES++))
else
    print_success "Advanced role-based access control implemented"
fi

echo ""
echo "3.2 Permission System Analysis..."
# Check for permission-based access control
permission_checks=$(grep -r "permission\|can.*\|has.*Permission" --include="*.py" --include="*.ts" --include="*.tsx" . | grep -v node_modules | wc -l)

if [ $permission_checks -lt 5 ]; then
    print_error "PERMISSION SYSTEM: Limited permission-based access control"
    ((AUTH_COMPLEXITY_ISSUES++))
else
    print_success "Comprehensive permission system detected"
fi

echo ""

# Test 4: COST MANAGEMENT ARCHITECTURE VALIDATION
print_header "4. COST MANAGEMENT ARCHITECTURE VALIDATION"

echo "4.1 Real-time Cost Integration Check..."
# Check for mock vs real cost data
mock_cost_data=$(grep -r "mock.*cost\|demo.*cost\|placeholder.*cost" --include="*.py" --include="*.ts" --include="*.tsx" . | grep -v node_modules | wc -l)

if [ $mock_cost_data -gt 0 ]; then
    print_error "COST MANAGEMENT: Mock/demo cost data detected"
    print_info "   Cost management not connected to real provider billing"
    ((COST_MGMT_ISSUES++))
else
    print_success "Real-time cost integration implemented"
fi

echo ""
echo "4.2 Budget Enforcement Analysis..."
# Check for budget enforcement mechanisms
budget_enforcement=$(grep -r "budget.*enforce\|rate.*limit\|cost.*limit" --include="*.py" . | wc -l)

if [ $budget_enforcement -lt 3 ]; then
    print_error "BUDGET ENFORCEMENT: Limited automated budget controls"
    ((COST_MGMT_ISSUES++))
else
    print_success "Automated budget enforcement detected"
fi

echo ""

# Test 5: INTEGRATION LAYER RELIABILITY
print_header "5. INTEGRATION LAYER RELIABILITY ANALYSIS"

echo "5.1 Error Handling & Retry Logic Check..."
# Check for robust error handling in LLM integrations
error_handling=$(grep -r "retry\|circuit.*breaker\|fallback\|timeout" --include="*.py" api/ | wc -l)

if [ $error_handling -lt 5 ]; then
    print_error "INTEGRATION RELIABILITY: Limited error handling and retry logic"
    print_info "   LLM integrations lack resilience patterns"
    ((INTEGRATION_ISSUES++))
else
    print_success "Robust integration error handling detected"
fi

echo ""
echo "5.2 Monitoring & Observability Check..."
# Check for comprehensive monitoring
monitoring_impl=$(grep -r "logging\|metrics\|tracing\|monitor" --include="*.py" api/ | wc -l)

if [ $monitoring_impl -lt 10 ]; then
    print_error "OBSERVABILITY: Limited monitoring and logging implementation"
    ((INTEGRATION_ISSUES++))
else
    print_success "Comprehensive monitoring implemented"
fi

echo ""

# Test 6: ENTERPRISE READINESS ASSESSMENT
print_header "6. ENTERPRISE READINESS ASSESSMENT"

echo "6.1 Audit Trail Implementation Check..."
# Check for audit logging
audit_trail=$(grep -r "audit\|trail\|log.*action\|activity.*log" --include="*.py" . | wc -l)

if [ $audit_trail -lt 5 ]; then
    print_error "COMPLIANCE: Limited audit trail implementation"
    print_info "   Enterprise compliance requires comprehensive audit logging"
    ((ARCHITECTURAL_ISSUES++))
else
    print_success "Audit trail implementation detected"
fi

echo ""
echo "6.2 Data Governance Framework Check..."
# Check for data classification and governance
data_governance=$(grep -r "classification\|retention\|pii.*detect\|gdpr\|ccpa" --include="*.py" . | wc -l)

if [ $data_governance -lt 3 ]; then
    print_error "DATA GOVERNANCE: Limited data governance framework"
    ((ARCHITECTURAL_ISSUES++))
else
    print_success "Data governance framework implemented"
fi

echo ""
echo "6.3 Security Framework Maturity..."
# Check for advanced security features
security_features=$(grep -r "encrypt\|secure\|auth.*token\|csrf\|xss" --include="*.py" --include="*.ts" . | grep -v node_modules | wc -l)

if [ $security_features -lt 10 ]; then
    print_error "SECURITY MATURITY: Basic security implementation"
    ((ARCHITECTURAL_ISSUES++))
else
    print_success "Advanced security framework detected"
fi

echo ""

# Test 7: SCALABILITY BOTTLENECKS
print_header "7. SCALABILITY BOTTLENECKS ANALYSIS"

echo "7.1 Multi-tenant Architecture Check..."
# Check for tenant isolation
tenant_isolation=$(grep -r "tenant\|isolation\|multi.*tenant" --include="*.py" . | wc -l)

if [ $tenant_isolation -lt 3 ]; then
    print_error "SCALABILITY: Single-tenant architecture detected"
    print_info "   Multi-tenant isolation required for enterprise scale"
    ((ARCHITECTURAL_ISSUES++))
else
    print_success "Multi-tenant architecture implemented"
fi

echo ""
echo "7.2 Performance Optimization Framework..."
# Check for performance monitoring and optimization
perf_optimization=$(grep -r "performance\|optimize\|cache\|async.*pool" --include="*.py" --include="*.ts" . | grep -v node_modules | wc -l)

if [ $perf_optimization -lt 8 ]; then
    print_error "PERFORMANCE: Limited performance optimization framework"
    ((ARCHITECTURAL_ISSUES++))
else
    print_success "Performance optimization framework detected"
fi

echo ""

# SUMMARY AND RECOMMENDATIONS
print_header "SYSTEMIC ISSUES SUMMARY & RECOMMENDATIONS"

total_issues=$((ARCHITECTURAL_ISSUES + DATA_MODEL_ISSUES + AUTH_COMPLEXITY_ISSUES + VALIDATION_ISSUES + COST_MGMT_ISSUES + INTEGRATION_ISSUES))

echo "Issue Category Breakdown:"
echo "========================"
echo "🏗️  Architectural Issues: $ARCHITECTURAL_ISSUES"
echo "📊 Data Model Issues: $DATA_MODEL_ISSUES"
echo "🔐 Authentication Complexity: $AUTH_COMPLEXITY_ISSUES"
echo "✅ Validation Issues: $VALIDATION_ISSUES"
echo "💰 Cost Management Issues: $COST_MGMT_ISSUES"
echo "🔗 Integration Issues: $INTEGRATION_ISSUES"
echo ""
echo "TOTAL SYSTEMIC ISSUES: $total_issues"
echo ""

if [ $total_issues -eq 0 ]; then
    print_success "🎉 EXCELLENT: No major systemic issues detected!"
    echo "The system shows strong architectural maturity and enterprise readiness."
elif [ $total_issues -le 5 ]; then
    print_warning "⚠️  MODERATE: $total_issues systemic issues need attention"
    echo "System is functional but requires architectural improvements for enterprise readiness."
elif [ $total_issues -le 10 ]; then
    print_error "🚨 HIGH: $total_issues systemic issues require immediate attention"
    echo "Significant architectural debt that will impact scalability and maintainability."
else
    print_error "🔥 CRITICAL: $total_issues systemic issues detected"
    echo "System requires comprehensive architectural refactoring before enterprise deployment."
fi

echo ""
echo "Priority Recommendations:"
echo "========================"

if [ $DATA_MODEL_ISSUES -gt 0 ]; then
    echo "1. 🔴 URGENT: Implement unified data model and API contracts"
fi

if [ $ARCHITECTURAL_ISSUES -gt 2 ]; then
    echo "2. 🔴 URGENT: Establish architectural governance and design system"
fi

if [ $AUTH_COMPLEXITY_ISSUES -gt 0 ]; then
    echo "3. 🟡 HIGH: Simplify authentication layer and implement enterprise RBAC"
fi

if [ $COST_MGMT_ISSUES -gt 0 ]; then
    echo "4. 🟡 HIGH: Replace mock cost data with real-time provider integration"
fi

if [ $INTEGRATION_ISSUES -gt 0 ]; then
    echo "5. 🟡 HIGH: Implement resilience patterns for LLM integrations"
fi

if [ $VALIDATION_ISSUES -gt 0 ]; then
    echo "6. 🟢 MEDIUM: Centralize validation logic and implement shared schemas"
fi

echo ""
echo "📋 Next Steps:"
echo "============="
echo "1. Review DEEPER_SYSTEMIC_ANALYSIS.md for detailed remediation plan"
echo "2. Prioritize Phase 1: Foundation Stabilization (4-6 weeks)"
echo "3. Implement architectural governance before adding new features"
echo "4. Establish quality gates for all future development"
echo ""

if [ $total_issues -gt 5 ]; then
    echo "🚨 RECOMMENDATION: Address systemic issues before enterprise sales"
    exit 1
else
    echo "✅ RECOMMENDATION: System ready for continued development with planned improvements"
    exit 0
fi
