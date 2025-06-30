#!/usr/bin/env python3
"""
Surgical script to fix remaining admin test route parameters
"""

import re

# Read admin test file
with open('/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py', 'r') as f:
    content = f.read()

# Pattern-based replacements that are safer
fixes = [
    # System maintenance tests - look for maintenance_data variable
    (r'(maintenance_data = {[^}]+}.*?)\n\s+# Create authenticated request using helper\n\s+req = create_auth_request\(method="POST"\)',
     r'\1\n\n        # Create authenticated request using helper\n        req = create_auth_request(method="POST", route_params={"resource": "system", "action": "maintenance"}, body=maintenance_data)'),
    
    # LLM settings GET - look for openai assertion
    (r'# Create authenticated request using helper\n\s+req = create_auth_request\(method="GET"\)\n\n\s+# Act\n\s+response = await admin_main\(req\)\n\n\s+# Assert\n\s+assert response\.status_code == 200\n\s+response_data = json\.loads\(response\.get_body\(\)\)\n\s+assert "openai" in response_data\["providers"\]',
     '# Create authenticated request using helper\n        req = create_auth_request(method="GET", route_params={"resource": "llm", "action": "settings"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "openai" in response_data["providers"]'),
    
    # LLM settings PUT - look for new_settings variable and specific assertion
    (r'(new_settings = {.*?}.*?)\n\s+# Create authenticated request using helper\n\s+req = create_auth_request\(method="PUT"\)\n\n\s+# Act\n\s+response = await admin_main\(req\)\n\n\s+# Assert\n\s+assert response\.status_code == 200\n\s+response_data = json\.loads\(response\.get_body\(\)\)\n\s+assert response_data\["message"\] == "LLM settings updated successfully"',
     r'\1\n\n        # Create authenticated request using helper\n        req = create_auth_request(method="PUT", route_params={"resource": "llm", "action": "settings"}, body=new_settings)\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["message"] == "LLM settings updated successfully"'),
    
    # Usage stats - look for totalRequests assertion  
    (r'# Create authenticated request using helper\n\s+req = create_auth_request\(method="GET"\)\n\n\s+# Act\n\s+response = await admin_main\(req\)\n\n\s+# Assert\n\s+assert response\.status_code == 200\n\s+response_data = json\.loads\(response\.get_body\(\)\)\n\s+assert "totalRequests" in response_data',
     '# Create authenticated request using helper\n        req = create_auth_request(method="GET", route_params={"resource": "usage"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "totalRequests" in response_data'),
    
    # Invalid role test - look for invalid_role_data variable
    (r'(invalid_role_data = {[^}]+}.*?)\n\s+# Create authenticated request using helper\n\s+req = create_auth_request\(method="PUT"\)',
     r'\1\n\n        # Create authenticated request using helper\n        req = create_auth_request(method="PUT", route_params={"resource": "users", "action": "role", "user_id": target_user_id}, body=invalid_role_data)'),
     
    # Test data endpoints - look for specific error messages
    (r'# Create authenticated request using helper\n\s+req = create_auth_request\(method="POST"\)\n\n\s+# Act\n\s+response = await admin_main\(req\)\n\n\s+# Assert\n\s+assert response\.status_code == 200\n\s+response_data = json\.loads\(response\.get_body\(\)\)\n\s+assert response_data\["message"\] == "Test data reset successfully"',
     '# Create authenticated request using helper\n        req = create_auth_request(method="POST", route_params={"resource": "system", "action": "reset-test-data"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["message"] == "Test data reset successfully"'),
     
    (r'# Create authenticated request using helper\n\s+req = create_auth_request\(method="POST"\)\n\n\s+# Act\n\s+response = await admin_main\(req\)\n\n\s+# Assert\n\s+assert response\.status_code == 200\n\s+response_data = json\.loads\(response\.get_body\(\)\)\n\s+assert response_data\["message"\] == "Test data seeded successfully"',
     '# Create authenticated request using helper\n        req = create_auth_request(method="POST", route_params={"resource": "system", "action": "seed-test-data"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["message"] == "Test data seeded successfully"'),
]

# Apply fixes
for pattern, replacement in fixes:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

# Write back
with open('/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py', 'w') as f:
    f.write(content)

print("Applied surgical route parameter fixes to admin tests!")
