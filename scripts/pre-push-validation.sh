#!/bin/bash
# Pre-Push Validation Script - Uses Unified Validation
# This ensures comprehensive testing before push
# Enhanced for product documentation alignment (PRD, Tech Spec, UX Guide)

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Pre-Push Validation...${NC}"
echo "Using unified validation script for comprehensive testing"
echo "Includes product documentation alignment validation"
echo ""

# Use unified validation in strict mode (matches CI/CD exactly)
exec "$SCRIPT_DIR/unified-validation.sh" strict all
