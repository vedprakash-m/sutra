#!/bin/bash
# Pre-Push Validation Script - Delegates to Unified Validation
# This ensures 100% parity between local and CI/CD validation

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Pre-Push Validation...${NC}"
echo "Using unified validation script for CI/CD parity"
echo ""

# Delegate to unified validation script in local mode
exec "$SCRIPT_DIR/unified-validation.sh" local all
