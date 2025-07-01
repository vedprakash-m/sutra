#!/usr/bin/env python3
"""
Simple script to fix specific admin test route parameters one by one.
"""

import re


def fix_specific_admin_tests():
    """Fix specific admin tests with exact replacements."""

    admin_test_file = "/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py"

    # Read the current content
    with open(admin_test_file, "r") as f:
        content = f.read()

    # Define exact fixes for specific test methods
    fixes = [
        # List users success - GET /api/admin/users
        {
            "find": 'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert len(response_data["users"]) == 2',
            "replace": 'req = create_auth_request(\n            method="GET",\n            route_params={"resource": "users"}\n        )\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert len(response_data["users"]) == 2',
        },
        # Update user role success - PUT /api/admin/users/{user_id}/role
        {
            "find": 'req = create_auth_request(\n            method="PUT", \n            route_params={"resource": "users", "action": "role", "user_id": target_user_id},\n            body=new_role_data\n        )\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200',
            "replace": 'req = create_auth_request(\n            method="PUT", \n            route_params={"resource": "users", "action": "role", "user_id": target_user_id},\n            body=new_role_data\n        )\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200',
        },
        # System health success - GET /api/admin/system/health
        {
            "find": 'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["status"] == "healthy"',
            "replace": 'req = create_auth_request(\n            method="GET",\n            route_params={"resource": "system", "action": "health"}\n        )\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["status"] == "healthy"',
        },
        # System stats success - GET /api/admin/system/stats
        {
            "find": 'req = create_auth_request(method="GET")\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["recent_activity"]["new_users"] == 5',
            "replace": 'req = create_auth_request(\n            method="GET",\n            route_params={"resource": "system", "action": "stats"}\n        )\n\n        # Act\n        response = await admin_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["recent_activity"]["new_users"] == 5',
        },
    ]

    # Apply fixes
    updated_content = content
    for fix in fixes:
        find_text = fix["find"]
        replace_text = fix["replace"]

        if find_text in updated_content:
            updated_content = updated_content.replace(find_text, replace_text)
            print(f"Applied fix for: {find_text[:30]}...")
        else:
            print(f"Could not find text: {find_text[:30]}...")

    # Write the updated content
    with open(admin_test_file, "w") as f:
        f.write(updated_content)

    print(f"Updated {admin_test_file}")


if __name__ == "__main__":
    fix_specific_admin_tests()
