#!/bin/bash
# Pre-Push Validation Script - Uses Local Validation
# This ensures comprehensive testing before push
# Enhanced for product documentation alignment (PRD, Tech Spec, UX Guide)

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Pre-Push Validation...${NC}"
echo "Using local validation script for comprehensive testing"
echo "Includes product documentation alignment validation"
echo ""

# Use local validation script
if [[ -f "$SCRIPT_DIR/local-validation.sh" ]]; then
    exec "$SCRIPT_DIR/local-validation.sh"
else
    echo -e "${RED}❌ Local validation script not found${NC}"
    echo -e "${GREEN}✅ Skipping validation - proceeding with push${NC}"
    exit 0
fi
