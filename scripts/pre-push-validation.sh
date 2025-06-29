#!/bin/bash
# Pre-Push Validation Script - Delegates to Local Validation
# This ensures comprehensive testing before push

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Pre-Push Validation...${NC}"
echo "Using local validation script for comprehensive testing"
echo ""

# Delegate to local validation script in strict mode
exec "$SCRIPT_DIR/local-validation.sh" --strict
