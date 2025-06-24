#!/bin/bash

# Bulk Test Authentication Fix Script
# This script updates test files to use the new Azure Static Web Apps authentication

echo "🔧 BULK TEST AUTHENTICATION FIXES"
echo "================================="
echo

# List of test files that need authentication fixes
TEST_FILES=(
    "api/admin_api/admin_test.py"
    "api/collections_api/collections_test.py" 
    "api/llm_execute_api/llm_execute_test.py"
    "api/playbooks_api/playbooks_test.py"
    "api/integrations_api/integrations_test.py"
)

for TEST_FILE in "${TEST_FILES[@]}"; do
    if [ -f "/Users/vedprakashmishra/sutra/$TEST_FILE" ]; then
        echo "🔧 Processing: $TEST_FILE"
        
        # Skip if file doesn't exist
        if [ ! -f "/Users/vedprakashmishra/sutra/$TEST_FILE" ]; then
            echo "   ⚠️  File not found, skipping"
            continue
        fi
        
        # Create a backup
        cp "/Users/vedprakashmishra/sutra/$TEST_FILE" "/Users/vedprakashmishra/sutra/$TEST_FILE.backup"
        
        # Check if file already has create_auth_request helper
        if ! grep -q "def create_auth_request" "/Users/vedprakashmishra/sutra/$TEST_FILE"; then
            echo "   ➕ Adding create_auth_request helper"
            
            # Add helper method (insert after class definition)
            sed -i '' '/class Test.*:/a\
\
    def create_auth_request(self, method="GET", body=None, route_params=None, params=None,\
                           user_id="test-user-123", role="user", url="http://localhost/api"):\
        """Helper to create authenticated requests for Azure Static Web Apps."""\
        import json\
        import base64\
        # Create user principal data\
        principal_data = {\
            "identityProvider": "azureActiveDirectory",\
            "userId": user_id,\
            "userDetails": "Test User",\
            "userRoles": [role],\
            "claims": []\
        }\
        \
        # Encode as base64\
        principal_b64 = base64.b64encode(json.dumps(principal_data).encode("utf-8")).decode("utf-8")\
        \
        # Create headers\
        headers = {\
            "x-ms-client-principal": principal_b64,\
            "x-ms-client-principal-id": user_id,\
            "x-ms-client-principal-name": "Test User",\
            "x-ms-client-principal-idp": "azureActiveDirectory"\
        }\
        if method in ["POST", "PUT"] and body:\
            headers["Content-Type"] = "application/json"\
        \
        return func.HttpRequest(\
            method=method,\
            url=url,\
            body=json.dumps(body).encode("utf-8") if body else b"",\
            headers=headers,\
            route_params=route_params or {},\
            params=params or {}\
        )
' "/Users/vedprakashmishra/sutra/$TEST_FILE"
        fi
        
        echo "   ✅ Processed: $TEST_FILE"
    fi
done

echo
echo "✅ Bulk fixes applied!"
echo "📋 Summary:"
echo "   - Added authentication helpers to test files"
echo "   - Backup files created with .backup extension"
echo
echo "⚠️  Manual steps still needed:"
echo "   1. Update individual tests to use self.create_auth_request()"
echo "   2. Remove old auth fixture dependencies"
echo "   3. Run pytest to verify fixes"
