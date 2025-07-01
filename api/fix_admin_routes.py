#!/usr/bin/env python3
"""
Quick script to systematically add route parameters to admin tests
"""

# Read admin test file
with open("/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py", "r") as f:
    content = f.read()

# Simple replacements for key patterns
replacements = [
    # Update user role tests
    (
        'req = create_auth_request(method="PUT")\n\n        # Act\n        response = await admin_main(req)',
        'req = create_auth_request(\n            method="PUT", \n            route_params={"resource": "users", "action": "role", "user_id": target_user_id},\n            body=new_role_data if "new_role_data" in locals() else invalid_role_data\n        )\n\n        # Act\n        response = await admin_main(req)',
    ),
    # System health tests
    (
        'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["status"] == "healthy"',
        'req = create_auth_request(method="GET", route_params={"resource": "system", "action": "health"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["status"] == "healthy"',
    ),
    # System stats tests
    (
        'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "totalUsers" in response_data',
        'req = create_auth_request(method="GET", route_params={"resource": "system", "action": "stats"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "totalUsers" in response_data',
    ),
    # Maintenance mode tests
    (
        'req = create_auth_request(method="POST")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200',
        'req = create_auth_request(method="POST", route_params={"resource": "system", "action": "maintenance"}, body=maintenance_data)\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200',
    ),
    # LLM settings tests
    (
        'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "openai" in response_data["providers"]',
        'req = create_auth_request(method="GET", route_params={"resource": "llm", "action": "settings"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "openai" in response_data["providers"]',
    ),
    (
        'req = create_auth_request(method="PUT")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["message"] == "LLM settings updated successfully"',
        'req = create_auth_request(method="PUT", route_params={"resource": "llm", "action": "settings"}, body=new_settings)\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["message"] == "LLM settings updated successfully"',
    ),
    # Usage stats tests
    (
        'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "totalRequests" in response_data',
        'req = create_auth_request(method="GET", route_params={"resource": "usage"})\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "totalRequests" in response_data',
    ),
]

# Apply replacements
for old, new in replacements:
    content = content.replace(old, new)

# Handle remaining generic GET requests that might need route_params={}
import re

content = re.sub(
    r'req = create_auth_request\(method="GET"\)\s*\n\s*# Act\s*\n\s*response = await admin_main\(req\)',
    'req = create_auth_request(method="GET", route_params={})\n\n        # Act\n        response = await admin_main(req)',
    content,
)

# Write back
with open("/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py", "w") as f:
    f.write(content)

print("Applied route parameter fixes to admin tests!")
