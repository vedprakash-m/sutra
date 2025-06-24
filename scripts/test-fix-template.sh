#!/bin/bash

# Quick Test Fix Template
# Apply this pattern to fix authentication in failing tests

echo "🔧 TEST AUTHENTICATION FIX TEMPLATE"
echo "===================================="
echo

cat << 'EOF'
# STEP 1: Add auth helper to test class (add after class definition)

def create_auth_request(self, method="GET", body=None, route_params=None, params=None, 
                       user_id="test-user-123", role="user", url="http://localhost/api"):
    """Helper to create authenticated requests for Azure Static Web Apps."""
    import json
    import base64
    
    # Create user principal data
    principal_data = {
        "identityProvider": "azureActiveDirectory", 
        "userId": user_id,
        "userDetails": "Test User",
        "userRoles": [role],
        "claims": []
    }
    
    # Encode as base64
    principal_b64 = base64.b64encode(json.dumps(principal_data).encode('utf-8')).decode('utf-8')
    
    # Create headers
    headers = {
        "x-ms-client-principal": principal_b64,
        "x-ms-client-principal-id": user_id,
        "x-ms-client-principal-name": "Test User", 
        "x-ms-client-principal-idp": "azureActiveDirectory"
    }
    if method in ["POST", "PUT"] and body:
        headers["Content-Type"] = "application/json"
    
    return func.HttpRequest(
        method=method,
        url=url,
        body=json.dumps(body).encode('utf-8') if body else b"",
        headers=headers,
        route_params=route_params or {},
        params=params or {}
    )

# STEP 2: Replace test method signatures (remove auth fixtures)

# OLD:
async def test_something(self, mock_auth_success, mock_cosmos_client):

# NEW:
async def test_something(self, mock_cosmos_client):

# STEP 3: Replace request creation

# OLD:
req = func.HttpRequest(
    method="POST",
    url="http://localhost/api/collections",
    body=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"},
    route_params={},
)

# NEW:
req = self.create_auth_request(
    method="POST",
    url="http://localhost/api/collections",
    body=data,
    user_id="test-user-123",
    role="user"
)

# STEP 4: Update test data to include required User fields

# OLD:
user_data = {
    "id": "user-123",
    "name": "Test User",
    "email": "test@example.com",
    "role": "user"
}

# NEW:
user_data = {
    "id": "user-123",
    "name": "Test User", 
    "email": "test@example.com",
    "role": "user",
    "created_at": "2025-06-15T09:00:00Z",
    "updated_at": "2025-06-15T09:00:00Z"
}

# STEP 5: Remove deprecated imports

# REMOVE these imports:
from api.shared.auth_mocking import (
    MockAuthContext,
    AuthMockingHelper, 
    StandardAuthMocks,
    mock_auth_success,
    mock_auth_failure
)

# ADD this import if missing:
import base64

EOF

echo
echo "🎯 QUICK COMMANDS TO FIX TESTS:"
echo

echo "# Fix a specific test:"
echo "pytest api/admin_api/admin_test.py::TestAdminAPI::test_specific_test -v"
echo

echo "# Check what tests are failing in a module:"
echo "pytest api/collections_api/ --tb=no | grep FAILED"
echo  

echo "# Test the auth system directly:"
echo "python -c \"from api.shared.auth_static_web_apps import create_mock_user; print(create_mock_user('test', 'admin'))\""
echo

echo "✅ WORKING EXAMPLES:"
echo "- api/health/ (8/8 tests passing)"
echo "- api/admin_api/admin_test.py::TestAdminAPI::test_list_users_success"  
echo "- api/collections_api/collections_test.py::TestCollectionsAPI::test_create_collection_success"
echo
