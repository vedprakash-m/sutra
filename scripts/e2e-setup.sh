#!/bin/bash

# E2E Setup Script - Simple wrapper for enhanced setup
# This provides the standard e2e:setup interface expected by package.json

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the enhanced setup script
exec "$SCRIPT_DIR/e2e-setup-enhanced.sh" "$@"
