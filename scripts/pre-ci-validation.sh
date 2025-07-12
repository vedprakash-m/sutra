#!/bin/bash

# Pre-CI Validation Script
# This script simulates the exact CI environment locally to catch issues before pushing
# It ensures 100% parity between local development and CI/CD environments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CI_SIMULATION_DIR="${PROJECT_ROOT}/.ci-simulation"

echo -e "${BLUE}🔍 Pre-CI Validation - Exact CI Environment Simulation${NC}"
echo -e "${CYAN}This script replicates the GitHub Actions CI environment locally${NC}"
echo -e "${CYAN}to catch issues before they appear in CI/CD${NC}"
echo ""

cd "$PROJECT_ROOT"

# Function to cleanup simulation environment
cleanup_simulation() {
    echo -e "${YELLOW}🧹 Cleaning up simulation environment...${NC}"
    rm -rf "$CI_SIMULATION_DIR" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Trap to ensure cleanup on exit
trap cleanup_simulation EXIT

# Create fresh simulation environment
echo -e "${BLUE}📦 Setting up CI simulation environment...${NC}"
rm -rf "$CI_SIMULATION_DIR"
mkdir -p "$CI_SIMULATION_DIR"

# Copy source code to simulation directory (excluding git and build artifacts)
echo -e "${CYAN}📋 Copying source code to simulation environment...${NC}"
rsync -av \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='.venv*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    --exclude='coverage.xml' \
    --exclude='.ci-simulation' \
    . "$CI_SIMULATION_DIR/"

cd "$CI_SIMULATION_DIR"

echo -e "${BLUE}🔧 Simulating CI Environment Setup...${NC}"

# Simulate GitHub Actions Node.js setup
echo -e "${CYAN}📦 Installing frontend dependencies (npm ci)...${NC}"
npm ci --prefer-offline --no-audit

# Simulate GitHub Actions Python setup  
echo -e "${CYAN}🐍 Installing backend dependencies...${NC}"
cd api
python3 -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Simulate pre-commit hooks
echo -e "${CYAN}🪝 Installing and running pre-commit hooks...${NC}"
pip install pre-commit
pre-commit run --all-files

# Run the unified validation in CI mode
echo -e "${BLUE}🚀 Running unified validation (CI mode)...${NC}"
./scripts/unified-validation.sh ci core

# Additional CI simulation checks
echo -e "${BLUE}🔍 Additional CI simulation checks...${NC}"

# Test frontend build (as done in CI)
echo -e "${CYAN}🏗️  Testing frontend build...${NC}"
npm run build

# Test build output verification (as done in CI)
echo -e "${CYAN}📁 Verifying build output...${NC}"
test -f dist/index.html || { echo -e "${RED}❌ dist/index.html not found${NC}"; exit 1; }
test -d dist/assets || { echo -e "${RED}❌ dist/assets directory not found${NC}"; exit 1; }

echo -e "${GREEN}✅ All CI simulation checks passed!${NC}"
echo -e "${GREEN}🎉 Your code should pass CI/CD pipeline${NC}"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "   1. Commit your changes"
echo -e "   2. Push to trigger CI/CD"
echo -e "   3. Monitor the CI/CD pipeline for any environment-specific issues"
