#!/bin/bash

# Authentication Migration Script
# Migrates all API endpoints from legacy JWT to Azure Static Web Apps authentication

set -e

echo "🔄 MIGRATING AUTHENTICATION TO AZURE STATIC WEB APPS"
echo "=================================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/api"

# Function to update import statements
update_imports() {
    local file="$1"
    echo "  📝 Updating imports in $file"

    # Replace legacy auth imports with static web apps imports
    sed -i.bak 's/from shared\.auth import.*$/from shared.auth_static_web_apps import require_auth, require_admin, get_current_user/' "$file"

    # Clean up backup file
    rm -f "${file}.bak"
}

# Function to update function decorators
update_decorators() {
    local file="$1"
    echo "  🔧 Updating decorators in $file"

    # This is a simplified migration - manual review will be needed
    # Replace common patterns
    sed -i.bak 's/@require_auth.*$/@require_auth(resource="api", action="read")/' "$file"
    sed -i.bak 's/@require_admin.*$/@require_admin/' "$file"

    # Clean up backup file
    rm -f "${file}.bak"
}

# Find all API endpoint files
echo "🔍 Finding API endpoints to migrate..."
api_endpoints=$(find "$API_DIR" -name "__init__.py" -not -path "*/shared/*" -not -path "*getroles*")

echo "Found $(echo "$api_endpoints" | wc -l) endpoints to migrate:"
echo "$api_endpoints"
echo ""

# Migrate each endpoint
for endpoint in $api_endpoints; do
    relative_path=$(echo "$endpoint" | sed "s|$PROJECT_ROOT/||")
    echo "🔄 Migrating $relative_path"

    # Check if file uses legacy auth
    if grep -q "from shared\.auth import" "$endpoint"; then
        update_imports "$endpoint"
        update_decorators "$endpoint"
        echo "  ✅ Updated $relative_path"
    else
        echo "  ⏭️  $relative_path doesn't use legacy auth - skipping"
    fi
    echo ""
done

echo "⚠️  MANUAL REVIEW REQUIRED"
echo "========================"
echo ""
echo "The following files have been automatically updated but require manual review:"
echo "$api_endpoints"
echo ""
echo "Please review each file to ensure:"
echo "1. Import statements are correct"
echo "2. Decorator parameters match the endpoint's requirements"
echo "3. User context access is updated (req.current_user instead of token parsing)"
echo "4. Role checking logic is updated"
echo ""
echo "Example patterns to look for:"
echo ""
echo "OLD PATTERN:"
echo "  user_id = get_user_id_from_token(req)"
echo "  if not check_admin_role(req):"
echo ""
echo "NEW PATTERN:"
echo "  user = await get_current_user(req)"
echo "  if not user or user.role != UserRole.ADMIN:"
echo ""
echo "After manual review, test each endpoint to ensure proper authentication."
